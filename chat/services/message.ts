import { ObjectId } from "mongodb";
import { MESSAGE_TYPE, STATUS } from "../enum";
import {
    TypeSendMessageRequest,
    TypeSendMessageResponse,
} from "../interface/message";
import mongoDb from "../mongoDb";
import Notification from "../notification";
import { checkUserActive, createLinkImage, getDateTimeNow } from "./assistant";

export const handleSendMessage = async (newMessage: TypeSendMessageRequest) => {
    const newMessageId = new ObjectId();

    const conversation = await mongoDb
        .collection("chat_conversation")
        .findOneAndUpdate(
            {
                _id: new ObjectId(newMessage.conversationId),
            },
            {
                $set: {
                    modified: getDateTimeNow(),
                    latest_message: newMessage.content,
                },
                $inc: {
                    total_messages: 1,
                },
            }
        );

    const insertMessage = {
        _id: newMessageId,
        type: newMessage.type,
        content: newMessage.content,
        creator: newMessage.creator,
        created: getDateTimeNow(),
        conversation_id: String(conversation.value?._id),
        status: STATUS.active,
    };

    await mongoDb.collection("chat_message").insertOne(insertMessage);

    // remake link image
    if (
        insertMessage.type === MESSAGE_TYPE.image &&
        Array.isArray(insertMessage.content)
    ) {
        const contentRemake = insertMessage.content.map((item) =>
            createLinkImage(item)
        );
        insertMessage.content = contentRemake;
    }

    const res: TypeSendMessageResponse = {
        id: String(newMessageId),
        conversationId: newMessage.conversationId,
        type: insertMessage.type,
        content: insertMessage.content,
        creator: insertMessage.creator,
        creatorName: newMessage.creatorName,
        creatorAvatar: newMessage.creatorAvatar,
        tag: newMessage.tag,
        created: String(insertMessage.created),
    };

    // Notification to partner if they not active
    const listUsers = conversation.value?.list_users;
    if (listUsers) {
        const partnerId = listUsers.find(
            (userId: number) => userId !== insertMessage.creator
        );
        if (partnerId) {
            const isPartnerNotActive = await checkUserActive(partnerId);
            if (isPartnerNotActive) {
                Notification.message({
                    creatorName: newMessage.creatorName,
                    message: newMessage.content,
                    receiver: partnerId,
                    conversationId: newMessage.conversationId,
                });
            }
        }
    }

    return res;
};
