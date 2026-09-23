// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title PassportRegistry
/// @notice On-chain target for Strategy Passport mint / revoke.
///
/// This file documents the contract that `backend/app/passport_backends/`
/// emits keccak256 hashes for. Not deployed at the hackathon; keccak
/// event topics match the hashes produced by `web3.keccak` in Python
/// so a deployed instance would accept the existing payloads without
/// re-signing or changing the Python adapter.
///
/// Event topic hashes (reproducible with keccak256):
///   PassportMinted(bytes16,bytes32,address,uint256)
///   PassportRevoked(bytes16,address,uint256)
contract PassportRegistry {
    event PassportMinted(
        bytes16 indexed passportId,
        bytes32 indexed specHash,
        address indexed minter,
        uint256 timestamp
    );

    event PassportRevoked(
        bytes16 indexed passportId,
        address indexed revoker,
        uint256 timestamp
    );

    mapping(bytes16 => address) public minterOf;
    mapping(bytes16 => bool) public revoked;
    mapping(address => uint256) public nonces;

    /// Mint a new passport. The passportId is keccak256(msg.sender,
    /// specHash, nonce) truncated to bytes16. Mirrors the on-chain
    /// shape produced by `backend/app/hash.py:short_id`, which uses
    /// `keccak256(canonical_json(spec))[:16]` from the Python side.
    /// We add `msg.sender` + `nonce` here so two users cannot collide
    /// on the same specHash in a deployed instance.
    function mint(bytes32 specHash) external returns (bytes16 passportId) {
        uint256 nonce = nonces[msg.sender]++;
        bytes memory packed = abi.encodePacked(msg.sender, specHash, nonce);
        passportId = bytes16(keccak256(packed));
        minterOf[passportId] = msg.sender;
        emit PassportMinted(passportId, specHash, msg.sender, block.timestamp);
    }

    /// Revoke an existing passport. Reverts if the caller is not the
    /// minter, the passport is unknown, or it has already been revoked.
    function revoke(bytes16 passportId) external {
        address minter = minterOf[passportId];
        require(minter != address(0), "unknown passport");
        require(minter == msg.sender, "not minter");
        require(!revoked[passportId], "already revoked");
        revoked[passportId] = true;
        emit PassportRevoked(passportId, msg.sender, block.timestamp);
    }

    /// Convenience read for off-chain indexers. Returns true if the
    /// passport is both known and not revoked.
    function isActive(bytes16 passportId) external view returns (bool) {
        return minterOf[passportId] != address(0) && !revoked[passportId];
    }
}