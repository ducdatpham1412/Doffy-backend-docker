import { Document, ObjectId, PushOperator } from "mongodb";
import { CHAT_TAG, MESSAGE_TYPE, TYPE_NOTIFICATION } from "../enum";
import {
    TypeAgreePublicChatParams,
    TypeHandleSeenMessage,
    TypeParamStartNewChatTag,
} from "../interface/chatTag";
import mongoDb from "../mongoDb";
import { executiveQuery } from "../mysqlDb";
import Notification from "../notification";
import {
    createLinkImage,
    getDateTimeNow,
    getListInfoUser,
    getUserIdFromToken,
} from "./assistant";

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
            creatorName: "",
            message: newChatTag.content,
            receiver: receiverId,
            conversationId: String(insertChatTag._id),
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

export const handleSeenMessage = async (params: TypeHandleSeenMessage) => {
    const { myId, conversationId } = params;

    const now = getDateTimeNow();
    const updateUserData = {
        [`user_data.${myId}.modified`]: now,
    };
    const conversation = await mongoDb
        .collection("chat_conversation")
        .findOneAndUpdate(
            {
                _id: new ObjectId(conversationId),
            },
            {
                $set: updateUserData,
            }
        );

    if (!conversation.value) {
        return;
    }

    return {
        conversationId,
        data: {
            [`${myId}`]: {
                modified: String(now),
            },
        },
    };
};
