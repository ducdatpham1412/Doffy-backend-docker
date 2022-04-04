export const SOCKET_EVENT = {
    // authenticate
    authenticate: "0.0",
    authenticateEnjoy: "0.1",
    unauthorized: "0.2",
    appActive: "0.3",
    appBackground: "0.4",
    // bubble
    addComment: "1.0",
    // chat tag
    createChatTag: "2.0",
    joinRoom: "2.1",
    leaveRoom: "2.1.1",
    requestPublicChat: "2.2",
    agreePublicChat: "2.3",
    allAgreePublicChat: "2.4",
    changeGroupName: "2.5",
    changeChatColor: "2.6",
    // message
    message: "3.0",
    messageEnjoy: "3.1",
    seenMessage: "3.2",
    deleteMessage: "3.3",
    typing: "3.4",
    unTyping: "3.5",
    // block or stop conversation
    isBlocked: "4.0",
    unBlocked: "4.1",
    stopConversation: "4.3",
    openConversation: "4.4",
    // notification
    notificationStartChatTag: "5.0",
    notificationFollow: "5.1",
    notificationLikePost: "5.2",
    notificationFriendPostNew: "5.3",
    notificationComment: "5.4",
};

export const CHAT_TAG = {
    newFromBubble: 0,
    newFromProfile: 1,
};

export const MESSAGE_TYPE = {
    text: 0,
    image: 1,
    sticker: 2,
};

export const TYPE_NOTIFICATION = {
    newChatTag: 0,
    follow: 1,
    likePost: 2,
    friendPostNew: 3,
};

export const GENDER = {
    male: 0,
    female: 1,
    notToSay: 2,
};
