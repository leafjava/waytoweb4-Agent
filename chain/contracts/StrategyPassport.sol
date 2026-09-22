// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
contract StrategyPassport {
    string public constant VERSION = "2-cents";
    enum Status { Active, Revoked }
    struct Passport { address author; bytes32 specHash; string leaderId; uint256 notionalCents; uint256 maxLossCents; uint64 expiry; bool humanConfirmed; Status status; }
    mapping(uint256 => Passport) public passports;
    uint256 public nextId = 1;
    event PassportMinted(uint256 indexed id, address indexed author, bytes32 specHash);
    event PassportRevoked(uint256 indexed id, address indexed by, string reasonCode);
    function mint(bytes32 specHash, string calldata leaderId, uint256 notionalCents, uint256 maxLossCents, uint64 expiry, bool humanConfirmed) external returns (uint256 id) {
        require(humanConfirmed, "confirmation required"); require(expiry > block.timestamp, "expired");
        require(notionalCents > 0 && maxLossCents > 0 && maxLossCents <= notionalCents, "invalid limits");
        require(bytes(leaderId).length > 0 && bytes(leaderId).length <= 64, "invalid leader");
        id = nextId++; passports[id] = Passport(msg.sender, specHash, leaderId, notionalCents, maxLossCents, expiry, humanConfirmed, Status.Active);
        emit PassportMinted(id, msg.sender, specHash);
    }
    function revoke(uint256 id, string calldata reasonCode) external {
        Passport storage p = passports[id]; require(p.author != address(0), "unknown passport"); require(msg.sender == p.author, "only author");
        if (p.status == Status.Revoked) return; p.status = Status.Revoked; emit PassportRevoked(id, msg.sender, reasonCode);
    }
}
