import { ObjectId } from "mongodb";
import { CHAT_TAG, MESSAGE_TYPE } from "../enum.js";
import mongoDb from "../mongoDb.js";
import Notification from "../notification.js";
import { request } from "../request.js";
import Static from "../static.js";
import {
    getListInfoUser,
    getUserIdFromToken,
    getDateTimeNow,
    createLinkImage,
} from "./assistant.js";

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
            groupName = `${name1} ${name2}`;
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

        // chat tag and message insert to mongo
        const insertChatTag = {
            listUser: listUserId,
            groupName,
            isPrivate,
            userSeenMessage,
            updateTime,
            type,
            color: newChatTag.color,
            listMessages: [
                {
                    _id: ObjectId(),
                    type: MESSAGE_TYPE.text,
                    content: newChatTag.content,
                    senderId: newChatTag.senderId,
                    createdTime: getDateTimeNow(),
                },
            ],
            totalMessages: 1,
        };
        await mongoDb.collection("chatTag").insertOne(insertChatTag);

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
        const newMessageId = ObjectId();
        const check = (
            await mongoDb.collection("chatTag").findOneAndUpdate(
                {
                    listUser: { $all: newChatTag.listUser },
                    type: CHAT_TAG.newFromProfile,
                },
                {
                    $set: { updateTime: getDateTimeNow() },
                    $push: {
                        listMessages: {
                            $each: [
                                {
                                    _id: newMessageId,
                                    type: MESSAGE_TYPE.text,
                                    content: newChatTag.content,
                                    senderId: newChatTag.senderId,
                                    createdTime: getDateTimeNow(),
                                },
                            ],
                            $position: 0,
                        },
                    },
                    $inc: {
                        totalMessages: 1,
                    },
                }
            )
        ).value;

        // if conversation from profile never exist before, change it to interact
        if (!check) {
            return await handleInteractBubble();
        }

        const responseMessage = {
            id: String(newMessageId),
            chatTag: newChatTag.chatTag,
            type: newMessage.type,
            content: newMessage.content,
            senderId: newMessage.senderId,
            senderAvatar: "",
            tag: "",
            createdTime: String(newMessage.createdTime),
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

    // Find latest message
    // let latestMessage = undefined;
    const chatTag = await mongoDb.collection("chatTag").findOne({
        _id: ObjectId(chatTagId),
    });

    const isMyChatTag = chatTag.listUser[0] === chatTag.listUser[1];
    const latestMessage = chatTag.listMessages.find((message) => {
        return isMyChatTag
            ? message.senderId === myId
            : message.senderId !== myId;
    });

    // update seen message of chat tag
    if (latestMessage) {
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
    }

    const res = {
        chatTagId,
        data: {
            [`${myId}`]: {
                latestMessage: String(latestMessage?._id || ""),
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
    return true;
};

export const handleChangeChatColor = async (params) => {
    const { token, newColor, chatTagId, socketId } = params;
    const userId = Static.getUserIdFromSocketId(socketId);
    if (!userId) return false;
    // user enjoy mode
    if (String(userId).includes("__")) {
        return true;
    }

    // user have account
    await request.put(
        `chat/change-chat-color/${chatTagId}`,
        {
            color: newColor,
        },
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
    );
    return true;
};

export const removeBubblePalaceFromDb = async (idBubble) => {
    await mongoDb.collection("bubblePalaceActive").deleteOne({
        _id: ObjectId(idBubble),
    });
};
