// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "forge-std/Script.sol";
import "../src/IntegrityAnchor.sol";

/**
 * @title DeployIntegrityAnchor
 * @notice Deployment script for the IntegrityAnchor contract.
 * @dev Usage:
 *   Local Anvil:  forge script script/DeployIntegrityAnchor.s.sol --rpc-url http://localhost:8545 --broadcast
 *   Sepolia:      forge script script/DeployIntegrityAnchor.s.sol --rpc-url $SEPOLIA_RPC_URL --broadcast --verify
 */
contract DeployIntegrityAnchor is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("ANCHOR_WALLET_PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        IntegrityAnchor anchor = new IntegrityAnchor();

        vm.stopBroadcast();

        // Log the deployed address for the backend to pick up
        console.log("IntegrityAnchor deployed at:", address(anchor));
    }
}
