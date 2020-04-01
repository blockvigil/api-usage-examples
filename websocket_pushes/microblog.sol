/*
 * Microblog Smart Contract.
 * Copyright 2019 Swaroop Hegde.
 * Code released under the MIT license.
*/

pragma solidity ^0.5.9;

contract Ownable {
    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }
}

contract Microblog is Ownable {
    struct Post {
        string title;
        string body;
        string url;
        string photo;
        uint time;
        bool isDead;
    }

    constructor(string memory _blogTitle, string memory _ownerName) Ownable() public {
        blogTitle = _blogTitle;
        ownerName = _ownerName;
    }

    string public blogTitle;
    string public ownerName;

    mapping (uint => Post ) posts;

    uint public lastPostId; //allows sequential iteration without having to store an expensive array

    event NewPost(uint id, string title, string photo); //helpful for webhooks

    function getPost(uint id) view public returns (string memory title, string memory body, string memory url, string memory photo, uint time, bool isDead){
        require(checkPost(id));
        title = posts[id].title;
        body = posts[id].body;
        url = posts[id].url;
        photo = posts[id].photo;
        time = posts[id].time;
        isDead = posts[id].isDead;
    }

    /*
     * Only Owners can add posts - EthVigil is the default owner and requires the API key to make write calls
    */
    function addPost(string memory title, string memory body, string memory url, string memory photo) onlyOwner public returns (uint){
        require(bytes(title).length > 0 && bytes(title).length <141); //Check if title is empty or larger than a tweet
        require(bytes(body).length <1001); //Check if body is too large
        /*
         *We want to check if the post was accidentally sent twice.
         *However, you may want to delete (setDead) a post and post again with the right content
        */
        require(posts[lastPostId].isDead == true || compare(title, posts[lastPostId].title) != 0);
        lastPostId = lastPostId+1;
        posts[lastPostId] = Post(title, body, url, photo, now, false);
        emit NewPost(lastPostId, title, photo);
        return lastPostId;
    }

    /*
     * We want to allow archiving a post if it was posted by mistake - it'll only set a flag, the post will continue to exist.
    */
    function setDead(uint id) onlyOwner public {
        require(checkPost(id));
        posts[id].isDead = true;
    }

    /*
     * Take control of the contract. Beware, once you change the owner, there's no going back.
     * EthVigil can no longer make write calls - get calls will still work.
    */
    function changeOwner(address newOwner) onlyOwner public returns (address){
        owner = newOwner;
        return owner;
    }

    function changeOwnerName(string memory _ownerName) onlyOwner public returns (string memory) {
        ownerName = _ownerName;
        return ownerName;
    }

    function changeBlogTitle(string memory _blogTitle) onlyOwner public returns (string memory) {
        blogTitle = _blogTitle;
        return blogTitle;
    }

    /*
     * Internal functions
    */

    function checkPost(uint id) view internal returns (bool){
        return bytes(posts[id].title).length > 0;
    }

    /*
     * Because there's no such thing as strings.. Internal function to compare strings borrowed from StringUtil
    */
    function compare(string memory _a, string memory _b) pure internal returns (int) {
        bytes memory a = bytes(_a);
        bytes memory b = bytes(_b);
        uint minLength = a.length;
        if (b.length < minLength) minLength = b.length;
        //@todo unroll the loop into increments of 32 and do full 32 byte comparisons
        for (uint i = 0; i < minLength; i ++)
            if (a[i] < b[i])
                return -1;
            else if (a[i] > b[i])
                return 1;
        if (a.length < b.length)
            return -1;
        else if (a.length > b.length)
            return 1;
        else
            return 0;
    }

}