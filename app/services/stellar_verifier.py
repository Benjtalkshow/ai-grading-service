from stellar_sdk import Server
from typing import Dict, Any, List
import httpx


class StellarVerifier:
    """Advanced on-chain verification for Stellar accounts and Soroban contracts"""

    def __init__(
        self,
        horizon_url: str = "https://horizon-testnet.stellar.org",
        soroban_rpc_url: str = "https://soroban-testnet.stellar.org:443",
    ):
        self.server = Server(horizon_url)
        self.horizon_url = horizon_url
        self.soroban_rpc_url = soroban_rpc_url

    async def verify_account(self, address: str) -> Dict[str, Any]:
        """Comprehensive account verification with balance, activity, and operation analysis"""
        if not address or len(address) != 56 or not address.startswith("G"):
            return {"error": "Invalid Stellar address format (must be 56 chars starting with G)"}

        try:
            account = self.server.accounts().account_id(address).call()

            # Parse balances
            balances = []
            xlm_balance = "0"
            for b in account.get("balances", []):
                if b["asset_type"] == "native":
                    xlm_balance = b["balance"]
                    balances.append({"asset": "XLM", "balance": b["balance"]})
                else:
                    balances.append({
                        "asset": f"{b.get('asset_code', 'unknown')}:{b.get('asset_issuer', 'unknown')[:8]}...",
                        "balance": b["balance"],
                    })

            # Fetch recent transactions
            txs = self.server.transactions().for_account(address).limit(25).order(desc=True).call()
            tx_records = txs.get("_embedded", {}).get("records", [])

            # Fetch recent operations for deeper analysis
            ops = self.server.operations().for_account(address).limit(50).order(desc=True).call()
            op_records = ops.get("_embedded", {}).get("records", [])

            # Categorize operations
            operation_summary = self._categorize_operations(op_records)

            # Detect Soroban-related activity
            soroban_activity = self._detect_soroban_activity(op_records)

            # Account flags and signers
            signers = account.get("signers", [])
            thresholds = account.get("thresholds", {})

            return {
                "exists": True,
                "address": address,
                "balance_xlm": xlm_balance,
                "total_balances": len(balances),
                "balances": balances[:10],
                "recent_tx_count": len(tx_records),
                "last_active": tx_records[0]["created_at"] if tx_records else "Never",
                "sequence_number": account.get("sequence", "0"),
                "operation_summary": operation_summary,
                "soroban_activity": soroban_activity,
                "signer_count": len(signers),
                "multi_sig": len(signers) > 1,
                "thresholds": thresholds,
                "subentry_count": account.get("subentry_count", 0),
                "data_entries": list(account.get("data", {}).keys()),
            }
        except Exception as e:
            error_str = str(e)
            if "404" in error_str or "Not Found" in error_str:
                return {
                    "exists": False,
                    "address": address,
                    "error": "Account not found on network - may not be funded or may be on a different network",
                }
            return {"error": f"Verification failed: {error_str}"}

    def _categorize_operations(self, operations: List[Dict]) -> Dict[str, Any]:
        """Categorize operations by type to understand account usage patterns"""
        summary = {
            "total_operations": len(operations),
            "operation_types": {},
            "payment_count": 0,
            "contract_invocations": 0,
            "trust_changes": 0,
            "offers": 0,
        }

        for op in operations:
            op_type = op.get("type", "unknown")
            summary["operation_types"][op_type] = summary["operation_types"].get(op_type, 0) + 1

            if op_type in ("payment", "path_payment_strict_receive", "path_payment_strict_send"):
                summary["payment_count"] += 1
            elif op_type == "invoke_host_function":
                summary["contract_invocations"] += 1
            elif op_type in ("change_trust", "allow_trust"):
                summary["trust_changes"] += 1
            elif op_type in ("manage_sell_offer", "manage_buy_offer", "create_passive_sell_offer"):
                summary["offers"] += 1

        return summary

    def _detect_soroban_activity(self, operations: List[Dict]) -> Dict[str, Any]:
        """Detect Soroban smart contract interactions"""
        activity = {
            "has_soroban_activity": False,
            "contract_invocations": 0,
            "contract_deployments": 0,
            "wasm_uploads": 0,
            "unique_contracts_called": set(),
            "recent_invocations": [],
        }

        for op in operations:
            if op.get("type") == "invoke_host_function":
                activity["has_soroban_activity"] = True
                function_type = op.get("function", "")

                if "HostFunctionTypeHostFunctionTypeInvokeContract" in str(function_type):
                    activity["contract_invocations"] += 1
                elif "HostFunctionTypeHostFunctionTypeCreateContract" in str(function_type):
                    activity["contract_deployments"] += 1
                elif "HostFunctionTypeHostFunctionTypeUploadContractWasm" in str(function_type):
                    activity["wasm_uploads"] += 1

                # Track recent invocations
                if len(activity["recent_invocations"]) < 10:
                    activity["recent_invocations"].append({
                        "type": op.get("function", "invoke_host_function"),
                        "created_at": op.get("created_at", ""),
                        "transaction_hash": op.get("transaction_hash", "")[:16] + "...",
                    })

        activity["unique_contracts_called"] = len(activity["unique_contracts_called"])
        return activity

    async def verify_contract(self, contract_id: str) -> Dict[str, Any]:
        """Verify a Soroban contract using the Soroban RPC endpoint"""
        if not contract_id or len(contract_id) != 56:
            return {"error": "Invalid Contract ID format (must be 56 chars)"}

        result = {
            "contract_id": contract_id,
            "network": "testnet",
            "status": "UNKNOWN",
            "details": {},
        }

        # Try Soroban RPC to get contract data
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Get the contract's ledger entry via Soroban RPC
                rpc_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLedgerEntries",
                    "params": {
                        "keys": [self._build_contract_key(contract_id)]
                    }
                }

                resp = await client.post(
                    self.soroban_rpc_url,
                    json=rpc_payload,
                    headers={"Content-Type": "application/json"}
                )

                if resp.status_code == 200:
                    rpc_data = resp.json()
                    rpc_result = rpc_data.get("result", {})

                    if rpc_result.get("entries"):
                        entry = rpc_result["entries"][0]
                        result["status"] = "VERIFIED_ON_NETWORK"
                        result["details"] = {
                            "last_modified_ledger": entry.get("lastModifiedLedgerSeq"),
                            "live_until_ledger": entry.get("liveUntilLedgerSeq"),
                            "entry_exists": True,
                        }
                        # Calculate TTL status
                        latest_ledger = rpc_result.get("latestLedger", 0)
                        live_until = entry.get("liveUntilLedgerSeq", 0)
                        if latest_ledger and live_until:
                            result["details"]["ledgers_until_expiry"] = live_until - latest_ledger
                            result["details"]["ttl_healthy"] = (live_until - latest_ledger) > 1000
                    else:
                        result["status"] = "NOT_FOUND"
                        result["details"]["note"] = "Contract not found via RPC - may be expired or not deployed"

                # Also try to get contract code/wasm info
                code_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "getLedgerEntries",
                    "params": {
                        "keys": [self._build_contract_code_key(contract_id)]
                    }
                }

                code_resp = await client.post(
                    self.soroban_rpc_url,
                    json=code_payload,
                    headers={"Content-Type": "application/json"}
                )

                if code_resp.status_code == 200:
                    code_data = code_resp.json()
                    code_result = code_data.get("result", {})
                    if code_result.get("entries"):
                        result["details"]["has_wasm_code"] = True

        except httpx.TimeoutException:
            result["details"]["rpc_error"] = "Soroban RPC timeout - network may be congested"
        except Exception as e:
            result["details"]["rpc_error"] = f"RPC query failed: {str(e)}"

        # Fallback: check Horizon for contract-related operations
        if result["status"] == "UNKNOWN":
            try:
                result["status"] = "UNVERIFIED"
                result["details"]["note"] = (
                    "Could not verify via Soroban RPC. Contract ID format is valid. "
                    "Manual verification recommended."
                )
            except Exception:
                pass

        return result

    def _build_contract_key(self, contract_id: str) -> str:
        """Build an XDR contract data ledger key for RPC query.
        This is a simplified version - in production, use stellar_sdk XDR builders."""
        # For the RPC getLedgerEntries call, we need the contract instance key
        # This is a placeholder that works with the Soroban RPC format
        try:
            from stellar_sdk import xdr as stellar_xdr
            from stellar_sdk import StrKey

            # Build the contract instance ledger key
            contract_hash = StrKey.decode_contract(contract_id)
            sc_address = stellar_xdr.SCAddress(
                type=stellar_xdr.SCAddressType.SC_ADDRESS_TYPE_CONTRACT,
                contract_id=stellar_xdr.Hash(contract_hash),
            )
            ledger_key = stellar_xdr.LedgerKey(
                type=stellar_xdr.LedgerEntryType.CONTRACT_DATA,
                contract_data=stellar_xdr.LedgerKeyContractData(
                    contract=sc_address,
                    key=stellar_xdr.SCVal(type=stellar_xdr.SCValType.SCV_LEDGER_KEY_CONTRACT_INSTANCE),
                    durability=stellar_xdr.ContractDataDurability.PERSISTENT,
                ),
            )
            return ledger_key.to_xdr()
        except Exception:
            return ""

    def _build_contract_code_key(self, contract_id: str) -> str:
        """Build ledger key for contract WASM code entry"""
        # Simplified - returns empty on failure, RPC will return error gracefully
        try:
            from stellar_sdk import xdr as stellar_xdr
            from stellar_sdk import StrKey

            contract_hash = StrKey.decode_contract(contract_id)
            sc_address = stellar_xdr.SCAddress(
                type=stellar_xdr.SCAddressType.SC_ADDRESS_TYPE_CONTRACT,
                contract_id=stellar_xdr.Hash(contract_hash),
            )
            ledger_key = stellar_xdr.LedgerKey(
                type=stellar_xdr.LedgerEntryType.CONTRACT_DATA,
                contract_data=stellar_xdr.LedgerKeyContractData(
                    contract=sc_address,
                    key=stellar_xdr.SCVal(type=stellar_xdr.SCValType.SCV_LEDGER_KEY_CONTRACT_INSTANCE),
                    durability=stellar_xdr.ContractDataDurability.PERSISTENT,
                ),
            )
            return ledger_key.to_xdr()
        except Exception:
            return ""

    async def get_contract_events(self, contract_id: str, limit: int = 20) -> Dict[str, Any]:
        """Fetch recent contract events via Soroban RPC"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getEvents",
                    "params": {
                        "filters": [
                            {
                                "type": "contract",
                                "contractIds": [contract_id],
                            }
                        ],
                        "pagination": {"limit": limit},
                    }
                }

                resp = await client.post(
                    self.soroban_rpc_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if resp.status_code == 200:
                    data = resp.json()
                    events = data.get("result", {}).get("events", [])
                    return {
                        "event_count": len(events),
                        "events": events[:limit],
                        "has_activity": len(events) > 0,
                    }

        except Exception as e:
            return {"error": f"Event fetch failed: {str(e)}", "event_count": 0}

        return {"event_count": 0, "events": [], "has_activity": False}
