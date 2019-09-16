pragma solidity >=0.5.1 <0.7.0;

contract SignerTesting {

    event ConfirmationSigRecieved(uint indexed uniqueID, address signer);
    event PrefixedHashGenerated(bytes32 hash);

    function submitConfirmation(uint256 uniqueID, bytes memory sig)
    public {
        bytes32 message = prefixed(keccak256(abi.encodePacked(uniqueID, address(this))));
        emit PrefixedHashGenerated(message);
        address signer = recoverSigner(message, sig);
        emit ConfirmationSigRecieved(uniqueID, signer);
    }

    function recoverSigner(bytes32 message, bytes memory sig) internal pure
    returns (address)
    {
        uint8 v;
        bytes32 r;
        bytes32 s;

        (v, r, s) = splitSignature(sig);

        return ecrecover(message, v, r, s);
    }

    function splitSignature(bytes memory sig)
    internal
    pure
    returns (uint8, bytes32, bytes32)
    {
        require(sig.length == 65);

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            // first 32 bytes, after the length prefix
            r := mload(add(sig, 32))
            // second 32 bytes
            s := mload(add(sig, 64))
            // final byte (first byte of the next 32 bytes)
            v := byte(0, mload(add(sig, 96)))
        }

        return (v, r, s);
    }

    // Builds a prefixed hash to mimic the behavior of eth_sign.
    function prefixed(bytes32 hash) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", hash));
    }
}