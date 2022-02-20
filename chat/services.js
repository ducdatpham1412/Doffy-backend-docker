import { ObjectId } from "mongodb";
import { CHAT_TAG, MESSAGE_TYPE } from "./enum.js";
import mongoDb from "./mongoDb.js";
import Notification from "./notification.js";
import { request } from "./request.js";
import Static from "./static.js";

/**
 * Authenticate
 */
export const getMyListChatTagsAndMyId = async (token) => {
  const res = await request.get("/auth/verify-token", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const myId = res.data;
  const listMyChatTag = await mongoDb
    .collection("chatTag")
    .find({
      listUser: myId,
    })
    .toArray();
  return { listMyChatTag, myId };
};

/**
 * Bubble
 */
export const increaseAndGetNumberBubbles = async () => {
  const temp = await mongoDb.collection("numberBubbles").findOneAndUpdate(
    {},
    {
      $inc: {
        number: 1,
      },
    }
  );
  return temp.value.number + 1;
};

export const getListSocketIdOfUserEnjoy = async () => {
  const res = await mongoDb
    .collection("userActive")
    .find({
      userId: {
        $regex: "__",
      },
    })
    .toArray();
  return res.map((item) => item.socketId);
};

/**
 * Chat tag
 */
export const handleStartNewChatTag = async (params) => {
  const { token, newChatTag } = params;
  const type = newChatTag.type;
  const isInteractBubble = type === CHAT_TAG.newFromBubble;
  const isMessageFromProfile = type === CHAT_TAG.newFromProfile;

  const handleInteractBubble = async () => {
    // info user
    const listUserId = newChatTag.listUser;
    listUserId.sort();
    const listInfoUser = await getListInfoUser({
      listUserId,
      displayAvatar: false,
      token,
    });

    // group name
    let groupName = "";
    if (isInteractBubble) groupName = newChatTag.nameBubble;
    else if (isMessageFromProfile) {
      const name1 = String(listInfoUser[0].name);
      const name2 = String(listInfoUser[1].name);
      groupName = name1.concat(" ").concat(name2);
    }

    const isPrivate = isInteractBubble;
    const updateTime = new Date();
    const userSeenMessage = {};
    listUserId.forEach((item) => {
      userSeenMessage[String(item)] = {
        latestMessage: "",
        isLatest: false,
      };
    });

    // chat tag to send socket to client
    const chatTag = {
      listUser: listInfoUser,
      groupName,
      isPrivate,
      userSeenMessage,
      updateTime,
      color: newChatTag.color,
    };

    // chat tag insert to mongo
    const insertChatTag = {
      listUser: listUserId,
      groupName,
      isPrivate,
      userSeenMessage,
      updateTime,
      type,
      color: newChatTag.color,
    };
    await mongoDb.collection("chatTag").insertOne(insertChatTag);

    // save the first message to mongo
    const newMessage = {
      chatTag: String(insertChatTag._id),
      type: MESSAGE_TYPE.text,
      content: newChatTag.content,
      senderId: newChatTag.senderId,
      createdTime: new Date(),
    };
    await mongoDb.collection("message").insertOne(newMessage);

    // Notification to receiver
    const receiver =
      listUserId.filter((item) => item != newChatTag.senderId)[0] ||
      listUserId[0]; // if not found id different senderId, get senderId
    await Notification.startNewChatTag({
      message: newChatTag.content,
      receiver,
      chatTagId: String(insertChatTag._id),
    });

    // Response
    const socketChatTag = {
      id: String(insertChatTag._id),
      ...chatTag,
      updateTime: String(chatTag.updateTime),
    };

    return {
      isChatTagExisted: false,
      response: socketChatTag,
    };
  };

  const handleSendFromProfile = async () => {
    const check = (
      await mongoDb.collection("chatTag").findOneAndUpdate(
        {
          listUser: { $all: newChatTag.listUser },
          type: CHAT_TAG.newFromProfile,
        },
        {
          $set: { updateTime: new Date() },
        }
      )
    ).value;

    // if conversation from profile never exist before, change it to interact
    if (!check) {
      return await handleInteractBubble();
    }

    // if conversation exited, only need to send socket message
    const newMessage = {
      chatTag: String(check._id),
      type: MESSAGE_TYPE.text,
      content: newChatTag.content,
      senderId: newChatTag.senderId,
      createdTime: new Date(),
    };
    await mongoDb.collection("message").insertOne(newMessage);

    const responseMessage = {
      id: String(newMessage._id),
      chatTag: newChatTag.chatTag,
      type: newMessage.type,
      content: newMessage.content,
      senderId: newMessage.senderId,
      senderAvatar: "",
      tag: "",
      createdTime: String(getDateTimeNow()),
    };

    return {
      isChatTagExisted: true,
      response: responseMessage,
    };
  };

  // control code
  if (isInteractBubble) {
    return await handleInteractBubble();
  } else if (isMessageFromProfile) {
    return await handleSendFromProfile();
  }
};

export const handleStartNewChatTagEnjoy = (params) => {
  const { myId, newChatTag } = params;

  const listUserId = newChatTag.listUser.sort();
  const listUserInfo = listUserId.map((userId) => ({
    id: userId,
    avatar: createLinkImage("__admin_girl.png"),
    name: "Name",
    gender: 1,
  }));
  const groupName = newChatTag.nameBubble;
  const isPrivate = true;
  const updateTime = getDateTimeNow();
  const userSeenMessage = {};
  listUserId.forEach((userId) => {
    userSeenMessage[String(userId)] = {
      latestMessage: "",
      isLatest: false,
    };
  });

  const responseChatTag = {
    id: String(ObjectId()),
    listUser: listUserInfo,
    groupName,
    isPrivate,
    userSeenMessage,
    updateTime: String(updateTime),
    color: newChatTag.color,
  };

  const responseMessage = {
    id: String(ObjectId()),
    chatTag: responseChatTag.id,
    type: MESSAGE_TYPE.text,
    content: newChatTag.content,
    senderId: myId,
    senderAvatar: createLinkImage("__admin_girl.png"),
    updateTime: String(updateTime),
  };

  return {
    newChatTag: responseChatTag,
    newMessage: responseMessage,
  };
};

export const getLatestMessage = async (params) => {
  const { myId, chatTagId } = params;

  // find latest message
  let latestMessage = undefined;
  latestMessage = (
    await mongoDb
      .collection("message")
      .find({
        chatTag: chatTagId,
        senderId: { $ne: myId },
      })
      .sort({ createdTime: -1 })
      .limit(1)
      .toArray()
  )[0];

  if (!latestMessage) {
    latestMessage = (
      await mongoDb
        .collection("message")
        .find({
          chatTag: chatTagId,
          senderId: myId,
        })
        .sort({ createdTime: -1 })
        .limit(1)
        .toArray()
    )[0];
  }
  if (!latestMessage) return;

  // update seen message of chat tag
  await mongoDb.collection("chatTag").findOneAndUpdate(
    {
      _id: ObjectId(chatTagId),
    },
    {
      $set: {
        [`userSeenMessage.${myId}`]: {
          latestMessage: String(latestMessage._id),
          isLatest: true,
        },
      },
    }
  );

  const res = {
    chatTagId,
    data: {
      [`${myId}`]: {
        latestMessage: String(latestMessage._id),
        isLatest: true,
      },
    },
  };

  return res;
};

export const handleRequestPublicChat = async (chatTagId) => {
  // save request to mongo
  await mongoDb.collection("requestPublicChat").findOneAndUpdate(
    {
      chatTag: chatTagId,
    },
    {
      $set: { listUserAgree: [] },
    },
    {
      upsert: true,
    }
  );

  // update time of chat tag
  await mongoDb.collection("chatTag").findOneAndUpdate(
    {
      _id: ObjectId(chatTagId),
    },
    {
      $set: { updateTime: getDateTimeNow() },
    }
  );
};

export const handleAgreePublicChat = async (params) => {
  const { token, chatTagId } = params;
  const userId = await getUserIdFromToken(token);

  // check all agree
  const infoChatTag = await mongoDb.collection("chatTag").findOne({
    _id: ObjectId(chatTagId),
  });
  if (!infoChatTag) return;

  const newRequest = await mongoDb
    .collection("requestPublicChat")
    .findOneAndUpdate(
      {
        chatTag: chatTagId,
      },
      {
        $push: { listUserAgree: userId },
      }
    );
  if (!newRequest.value) return;

  const listUserOfChatTag = infoChatTag.listUser.sort();
  const listUserAgree = newRequest.value.listUserAgree.concat(userId).sort();
  if (JSON.stringify(listUserOfChatTag) !== JSON.stringify(listUserAgree))
    return;

  // handle public chat tag
  // if all agree, get real info of list user and send back client
  const publicTime = getDateTimeNow();

  await mongoDb.collection("chatTag").findOneAndUpdate(
    {
      _id: ObjectId(chatTagId),
    },
    {
      $set: {
        isPrivate: false,
        updateTime: publicTime,
      },
    }
  );

  const listInfoUser = await getListInfoUser({
    listUserId: infoChatTag.listUser,
    displayAvatar: true,
    token,
  });

  const updateChatTag = {
    id: chatTagId,
    listUser: listInfoUser,
    groupName: infoChatTag.groupName,
    isPrivate: false,
    isStop: false,
    isBlock: false,
    userSeenMessage: infoChatTag.userSeenMessage,
    type: infoChatTag.type,
    updateTime: publicTime,
  };

  return updateChatTag;
};

export const changeGroupName = async (params) => {
  const { token, chatTagId, newName } = params;
  try {
    await request.put(
      `chat/change-group-name/${chatTagId}`,
      {
        name: newName,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
  } catch (err) {
    // user enjoy mode - token not valid
    console.log("change group name for enjoy mode: ", chatTagId);
  }
};

/**
 * Message
 */
export const handleSendMessage = async (newMessage) => {
  const insertMessage = {
    chatTag: newMessage.chatTag,
    type: newMessage.type,
    content: newMessage.content,
    senderId: newMessage.senderId,
    createdTime: getDateTimeNow(),
  };
  await mongoDb.collection("message").insertOne(insertMessage);

  // remake link image
  if (insertMessage.type === MESSAGE_TYPE.image) {
    const contentRemake = insertMessage.content.map((item) =>
      createLinkImage(item)
    );
    insertMessage.content = contentRemake;
  }

  const res = {
    id: String(insertMessage._id),
    chatTag: insertMessage.chatTag,
    type: insertMessage.type,
    content: insertMessage.content,
    senderId: insertMessage.senderId,
    senderAvatar: newMessage.senderAvatar,
    tag: newMessage.tag,
    createdTime: String(insertMessage.createdTime),
  };

  // update status is latest of other member
  const partnerId =
    newMessage.listUser[0] !== insertMessage.senderId
      ? newMessage.listUser[0]
      : newMessage.listUser[1];
  await mongoDb.collection("chatTag").findOneAndUpdate(
    {
      _id: ObjectId(insertMessage.chatTag),
    },
    {
      $set: {
        [`userSeenMessage.${partnerId}.isLatest`]: false,
        updateTime: getDateTimeNow(),
      },
    }
  );

  // Notification to partner if they not active
  const isPartnerNotActive = !Static.checkIncludeUserId(partnerId);
  if (isPartnerNotActive) {
    Notification.message({
      senderName: newMessage.groupName,
      message: newMessage.content,
      receiver: partnerId,
      chatTagId: insertMessage.chatTag,
    });
  }

  return res;
};

export const handleSendMessageEnjoy = (newMessage) => {
  return {
    id: String(ObjectId()),
    ...newMessage,
    createdTime: String(getDateTimeNow()),
  };
};

/**
 * Helper function
 */
export const getSocketIdOfListUserActive = async (listUserId) => {
  const result = [];
  const listUniqueId = filterTheSame(listUserId);
  for (let i = 0; i < listUniqueId.length; i++) {
    const check = await mongoDb
      .collection("userActive")
      .findOne({ userId: listUniqueId[i] });
    if (check) result.push(check.socketId);
  }
  return result;
};

const getListInfoUser = async ({ listUserId, displayAvatar, token }) => {
  const res = await request.post(
    "/chat/list-info-user",
    {
      listUserId,
      displayAvatar,
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return res.data;
};

const getUserIdFromToken = async (token) => {
  const res = await request.get("auth/verify-token", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return res.data;
};

const filterTheSame = (originArray) => {
  const res = originArray.filter((item, index, self) => {
    return self.indexOf(item) === index;
  });
  return Array.from(res);
};

const getDateTimeNow = () => {
  return new Date();
};

const createLinkImage = (imageName) => {
  return `https://doffy.s3.ap-southeast-1.amazonaws.com/image/${imageName}`;
};
