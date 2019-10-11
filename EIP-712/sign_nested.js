function parseSignature(signature) {
  var r = signature.substring(0, 64);
  var s = signature.substring(64, 128);
  var v = signature.substring(128, 130);

  return {
      r: "0x" + r,
      s: "0x" + s,
      v: parseInt(v, 16)
  }
}

window.onload = function (e) {
  var res = document.getElementById("response");
  res.style.display = "none";

  // force the user to unlock their MetaMask
  if (web3.eth.accounts[0] == null) {
    alert("Please unlock MetaMask first");
    // Trigger login request with MetaMask
    web3.currentProvider.enable().catch(alert)
  }

  var signBtn = document.getElementById("signBtn");
  signBtn.onclick = function(e) {
    if (web3.eth.accounts[0] == null) {
      return;
    }

    const domain = [
      { name: "name", type: "string" },
      { name: "version", type: "string" },
      { name: "chainId", type: "uint256" },
      { name: "verifyingContract", type: "address" }
    ];

    const unit_type = [
      { name: 'actionType', type: 'string' },
      { name: 'timestamp', type: 'uint256' },
      { name: 'authorizer', type: 'Identity' }
    ];

    const identity_type = [
      { name: "userId", type: "uint256" },
      { name: "wallet", type: "address" },
    ];

    const chainId = 5;

    const domainData = {
      name: "VerifierApp101",
      version: "1",
      chainId: chainId,
      verifyingContract: "0x8c1eD7e19abAa9f23c476dA86Dc1577F1Ef401f5"
    };


    var message = {
        actionType: 'Action7440',
        timestamp: 1570112162,
        authorizer: {
            userId: 123,
            wallet: '0x00EAd698A5C3c72D5a28429E9E6D6c076c086997'
        }
    }; // order of the fields is is important. Should correspond to the tuple type expected on the contract.

    const data = JSON.stringify({
      types: {
        EIP712Domain: domain,
        Unit: unit_type,
        Identity: identity_type,
      },
      domain: domainData,
      primaryType: "Unit",
      message: message
    });

    const signer = web3.toChecksumAddress(web3.eth.accounts[0]);

    web3.currentProvider.sendAsync(
      {
        method: "eth_signTypedData_v3",
        params: [signer, data],
        from: signer
      },
      function(err, result) {
        if (err || result.error) {
          return console.error(result);
        }

        const signature = parseSignature(result.result.substring(2));

        res.style.display = "block";
        res.value = "SigR: "+signature.r+"\nSigS: "+signature.s+"\nSigV: "+signature.v+"\nSigner: "+signer;

        var xhr = new XMLHttpRequest();
        var url = 'http://localhost:6635/nested'
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");

        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
                window.alert('Submitted succesfully. Check tornado backend logs and console logs.')
                console.log(json)
            }
        };

        var data = JSON.stringify({
            command: 'submitApproval',
            // replace the following with the deployed EIP712NestedStruct.sol contract address
            contractAddress: '0x21f0f61eb0ce57374b1a3d053940f32e7f2e478b',
            messageObject: message,
            sigR: signature.r,
            sigS: signature.s,
            sigV: signature.v,
            signer: signer

        });

        xhr.send(data);
      }
    );
  };
}