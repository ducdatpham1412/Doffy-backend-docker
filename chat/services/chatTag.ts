import { ObjectId } from "mongodb";
import { COLOR, CONVERSATION_STATUS, MESSAGE_TYPE, STATUS } from "../enum";
import {
    TypeChatTagResponse,
    TypeCreateChatTag,
    TypeHandleSeenMessage,
} from "../interface/chatTag";
import mongoDb from "../mongoDb";
import Notification from "../notification";
import { request } from "../request";
import { TypeSendMessageResponse } from "./../interface/message.d";
import {
    checkUserActive,
    createLinkImage,
    getDateTimeNow,
    getListInfoUser,
    getUserIdFromToken,
} from "./assistant";

const getRandomColor = () => {
    const check = Object.values(COLOR);
    const indexRandom = Math.floor(Math.random() * check.length);
    return Number(check[indexRandom]);
};

export const handleStartConversation = async (params: TypeCreateChatTag) => {
    const { token, conversation } = params;
    const myId = await getUserIdFromToken(token);
    const now = getDateTimeNow();

    // Check can send message to this user
    // If is locking or block, will raise Error
    await request.get(
        `/profile/check-block-lock-account/${conversation.userId}`,
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
    );

    const listUsersInfo = await getListInfoUser({
        listUserId: [myId, conversation.userId],
        token,
    });
    const partnerInfo = listUsersInfo.find(
        (item) => item.id === conversation.userId
    );
    const myInfo = listUsersInfo.find((item) => item.id === myId);
    if (!partnerInfo || !myInfo) {
        return;
    }

    const listUsers = [myId, conversation.userId].sort();
    const checkConversation = await mongoDb
        .collection("chat_conversation")
        .findOneAndUpdate(
            {
                list_users: listUsers,
            },
            {
                $set: {
                    modified: now,
                    latest_message: conversation.content,
                },
                $inc: {
                    total_messages: 1,
                },
            }
        );

    /**
     * Conversation between two people existed before
     */
    if (checkConversation.value) {
        const insertMessage = {
            _id: new ObjectId(),
            type: MESSAGE_TYPE.text,
            content: conversation.content,
            creator: myId,
            created: now,
            conversation_id: String(checkConversation.value._id),
            status: STATUS.active,
        };
        await mongoDb.collection("chat_message").insertOne(insertMessage);

        const resMessage: TypeSendMessageResponse = {
            id: String(insertMessage._id),
            conversationId: insertMessage.conversation_id,
            type: insertMessage.type,
            content: insertMessage.content,
            creator: insertMessage.creator,
            creatorName: partnerInfo.name,
            creatorAvatar: createLinkImage(partnerInfo.avatar),
            tag: undefined,
            created: String(insertMessage.created),
        };

        const isPartnerNotActive = await checkUserActive(partnerInfo.id);
        if (isPartnerNotActive) {
            Notification.message({
                creatorName: myInfo.name,
                message: insertMessage.content,
                receiver: partnerInfo.id,
                conversationId: insertMessage.conversation_id,
            });
        }

        return {
            isExisted: true,
            data: resMessage,
        };
    }

    /**
     * Start new conversation
     */
    const color = getRandomColor();
    const userData: any = {};
    listUsers.forEach((userId) => {
        userData[String(userId)] = {
            created: "start",
            modified: new Date(now.getTime() - 2 * 60000),
        };
    });
    const insertConversation: any = {
        list_users: listUsers,
        conversation_name: "",
        conversation_image: "",
        color,
        created: now,
        modified: now,
        user_data: userData,
        total_messages: 1,
        latest_message: conversation.content,
        status: CONVERSATION_STATUS.active,
    };
    await mongoDb.collection("chat_conversation").insertOne(insertConversation);

    const insertMessage = {
        type: MESSAGE_TYPE.text,
        content: conversation.content,
        creator: myId,
        created: now,
        conversation_id: String(insertConversation._id),
        status: STATUS.active,
    };
    await mongoDb.collection("chat_message").insertOne(insertMessage);

    const resConversation: TypeChatTagResponse = {
        id: String(insertConversation._id),
        listUser: listUsersInfo,
        conversationName: "",
        conversationImage: "",
        userData: userData,
        color,
        modified: String(now),
        isBlocked: false,
        latestMessage: conversation.content,
        status: insertConversation.status,
    };

    const isPartnerNotActive = await checkUserActive(partnerInfo.id);
    if (isPartnerNotActive) {
        Notification.message({
            creatorName: myInfo.name,
            message: insertMessage.content,
            receiver: partnerInfo.id,
            conversationId: insertMessage.conversation_id,
        });
    }

    return {
        isExisted: false,
        data: resConversation,
    };
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
