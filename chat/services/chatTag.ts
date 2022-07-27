import { Document, ObjectId, PushOperator } from "mongodb";
import { CHAT_TAG, MESSAGE_TYPE, TYPE_NOTIFICATION } from "../enum";
import mongoDb from "../mongoDb";
import Notification from "../notification";
import { request } from "../request";
import Static from "../static";
import {
    getListInfoUser,
    getUserIdFromToken,
    getDateTimeNow,
    createLinkImage,
} from "./assistant";
import { executiveQuery } from "../mysqlDb";
import {
    TypeAgreePublicChatParams,
    TypeChangeColorParams,
    TypeChangeGroupNameParams,
    TypeParamsGetLatestMessage,
    TypeParamStartNewChatTag,
} from "../interface/chatTag";

export const handleStartNewChatTag = async (
    params: TypeParamStartNewChatTag
) => {
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
        if (isInteractBubble) groupName = newChatTag?.nameBubble || "";
        else if (isMessageFromProfile) {
            const name1 = String(listInfoUser[0].name);
            const name2 = String(listInfoUser[1].name);
            groupName = `${name1} ${name2}`;
        }

        const isPrivate = isInteractBubble;
        const updateTime = new Date();
        const userSeenMessage: any = {};
        listUserId.forEach((item: number) => {
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
        const insertChatTag: any = {
            listUser: listUserId,
            groupName,
            isPrivate,
            userSeenMessage,
            updateTime,
            type,
            color: newChatTag.color,
            listMessages: [
                {
                    _id: new ObjectId(),
                    type: MESSAGE_TYPE.text,
                    content: newChatTag.content,
                    senderId: newChatTag.senderId,
                    createdTime: getDateTimeNow(),
                },
            ],
            totalMessages: 1,
        };
        await mongoDb.collection("chatTag").insertOne(insertChatTag);

        // If this is chat from bubble, decrease the priority of profilePost
        if (isInteractBubble) {
            const idBubble = newChatTag.idBubble;
            await mongoDb.collection("profilePost").findOneAndUpdate(
                {
                    _id: new ObjectId(idBubble),
                },
                {
                    $inc: {
                        priority: 1,
                    },
                }
            );
        }

        // Notification to receiverId
        const receiverId =
            listUserId.filter(
                (item: number) => item != newChatTag.senderId
            )[0] || listUserId[0]; // if not found id different senderId, get senderId
        await Notification.startNewChatTag({
            message: newChatTag.content,
            receiver: receiverId,
            chatTagId: String(insertChatTag._id),
        });

        // Data and Socket notification
        const selectedName = isInteractBubble ? "anonymous_name" : "name";
        const query = `SELECT ${selectedName} AS name, avatar FROM myprofile_profile WHERE user_id = ${newChatTag.senderId}`;
        const profileSender = (await executiveQuery(query))[0];
        const content = `${profileSender.name} làm quen với bạn này 😇`;

        let senderAvatar = "";
        if (isInteractBubble) {
            const temp = listInfoUser.find(
                (item) => item.id === newChatTag.senderId
            );
            senderAvatar = temp?.avatar || "";
        } else {
            senderAvatar = createLinkImage(profileSender.avatar || "");
        }

        const dataNotification = {
            id: String(new ObjectId()),
            type: TYPE_NOTIFICATION.newChatTag,
            content,
            image: senderAvatar,
            chatTagId: String(insertChatTag._id),
            hadRead: false,
        };
        mongoDb.collection("notification").findOneAndUpdate(
            {
                userId: receiverId,
            },
            {
                $push: {
                    list: {
                        $each: [dataNotification],
                        $position: 0,
                    },
                } as unknown as PushOperator<Document>,
            }
        );

        // Response
        const socketChatTag = {
            id: String(insertChatTag._id),
            chatTag: String(insertChatTag._id),
            ...chatTag,
            updateTime: String(chatTag.updateTime),
        };

        return {
            isChatTagExisted: false,
            response: socketChatTag,
            dataNotification,
        };
    };

    const handleSendFromProfile = async () => {
        const newMessageId = new ObjectId();
        const currentTime = getDateTimeNow();
        const check = (
            await mongoDb.collection("chatTag").findOneAndUpdate(
                {
                    listUser: newChatTag.listUser.sort(),
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
                                    createdTime: currentTime,
                                },
                            ],
                            $position: 0,
                        },
                    } as unknown as PushOperator<Document>,
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
            chatTag: String(check._id),
            listUser: undefined,
            type: MESSAGE_TYPE.text,
            content: newChatTag.content,
            senderId: newChatTag.senderId,
            senderAvatar: "",
            tag: "",
            createdTime: currentTime,
        };

        return {
            isChatTagExisted: true,
            response: responseMessage,
            dataNotification: undefined,
        };
    };

    // control code
    if (isInteractBubble) {
        return await handleInteractBubble();
    } else if (isMessageFromProfile) {
        return await handleSendFromProfile();
    }
};

export const getLatestMessage = async (params: TypeParamsGetLatestMessage) => {
    const { myId, chatTagId } = params;

    // Find latest message
    // let latestMessage = undefined;
    const chatTag = await mongoDb.collection("chatTag").findOne({
        _id: new ObjectId(chatTagId),
    });

    if (!chatTag) {
        return null;
    }

    const isMyChatTag = chatTag.listUser[0] === chatTag.listUser[1];
    const latestMessage = chatTag.listMessages.find((message: any) => {
        return isMyChatTag
            ? message.senderId === myId
            : message.senderId !== myId;
    });

    // update seen message of chat tag
    if (latestMessage) {
        await mongoDb.collection("chatTag").findOneAndUpdate(
            {
                _id: new ObjectId(chatTagId),
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

export const handleRequestPublicChat = async (chatTagId: string) => {
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
            _id: new ObjectId(chatTagId),
        },
        {
            $set: { updateTime: getDateTimeNow() },
        }
    );
};

export const handleAgreePublicChat = async (
    params: TypeAgreePublicChatParams
) => {
    const { token, chatTagId } = params;
    const userId = await getUserIdFromToken(token);

    // check all agree
    const infoChatTag = await mongoDb.collection("chatTag").findOne({
        _id: new ObjectId(chatTagId),
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
            _id: new ObjectId(chatTagId),
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

export const changeGroupName = async (params: TypeChangeGroupNameParams) => {
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

export const handleChangeChatColor = async (params: TypeChangeColorParams) => {
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
