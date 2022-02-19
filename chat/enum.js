export const SOCKET_EVENT = {
  // authenticate
  authenticate: "1",
  authenticateEnjoy: "1.0",
  unauthorized: "2",
  appActive: "1.3",
  appBackground: "1.4",
  // bubble
  createBubble: "3.0",
  deleteBubble: "3.5",
  // chat tag
  createChatTag: "4",
  joinRoom: "4.1",
  requestPublicChat: "4.2",
  agreePublicChat: "4.3",
  allAgreePublicChat: "4.4",
  // message
  message: "5",
  messageEnjoy: "5.1",
  seenMessage: "6",
  // block or stop conversation
  isBlocked: "9",
  unBlocked: "10",
  changeGroupName: "11",
  stopConversation: "12",
  openConversation: "13",
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
  message: 1,
  follow: 2,
};
