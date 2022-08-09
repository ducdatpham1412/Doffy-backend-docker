export enum SOCKET_EVENT {
    // authenticate
    authenticate = "0.0",
    authenticateEnjoy = "0.1",
    unauthorized = "0.2",
    appActive = "0.3",
    appBackground = "0.4",
    // bubble
    addComment = "1.0",
    joinCommunity = "1.1",
    hadNewUserJoinCommunity = "1.2",
    // chat tag
    createChatTag = "2.0",
    joinRoom = "2.1",
    leaveRoom = "2.2",
    changeChatName = "2.3",
    changeChatColor = "2.4",
    // message
    message = "3.0",
    messageEnjoy = "3.1",
    seenMessage = "3.2",
    deleteMessage = "3.3",
    typing = "3.4",
    unTyping = "3.5",
    // block or stop conversation
    isBlocked = "4.0",
    unBlocked = "4.1",
    stopConversation = "4.3",
    openConversation = "4.4",
    // notification
    notification = "5.0",
}

export const CHAT_TAG = {
    newFromBubble: 0,
    newFromProfile: 1,
    group: 2,
};

export const MESSAGE_TYPE = {
    text: 0,
    image: 1,
    sticker: 2,
    joinCommunity: 3,
    changeColor: 4,
    changeName: 5,
};

export const TYPE_NOTIFICATION = {
    newChatTag: 0,
    follow: 1,
    likePost: 2,
    friendPostNew: 3,
    comment: 4,
    message: 5,
};

export const GENDER = {
    male: 0,
    female: 1,
    notToSay: 2,
};

export const STATUS = {
    active: 1,
    notActive: 0,
};

export enum CONVERSATION_STATUS {
    active = 1,
    stop = 0,
}

export const COLOR = {
    talking: 1,
    movie: 2,
    technology: 3,
    gaming: 4,
    animal: 5,
    travel: 6,
    fashion: 7,
    other: 8,
};
