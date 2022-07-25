import { Document, ObjectId, PushOperator } from "mongodb";
import { MESSAGE_TYPE } from "../enum";
import { TypeSendMessageRequest } from "../interface/message";
import mongoDb from "../mongoDb";
import Notification from "../notification";
import Static from "../static";
import { getDateTimeNow, createLinkImage } from "./assistant";

export const handleSendMessage = async (newMessage: TypeSendMessageRequest) => {
    const newMessageId = new ObjectId();

    const insertMessage = {
        _id: newMessageId,
        type: newMessage.type,
        content: newMessage.content,
        senderId: newMessage.senderId,
        createdTime: getDateTimeNow(),
    };

    const partnerId =
        newMessage.listUser[0] !== insertMessage.senderId
            ? newMessage.listUser[0]
            : newMessage.listUser[1];

    const setUpdate: any = {};
    newMessage.listUser.forEach((userId) => {
        if (userId !== insertMessage.senderId) {
            setUpdate[`userSeenMessage.${userId}.istLatest`] = false;
        }
    });

    await mongoDb.collection("chatTag").findOneAndUpdate(
        {
            _id: new ObjectId(newMessage.chatTag),
        },
        {
            $set: {
                ...setUpdate,
                updateTime: getDateTimeNow(),
            },
            $push: {
                listMessages: {
                    $each: [insertMessage],
                    $position: 0,
                },
            } as unknown as PushOperator<Document>,
            $inc: {
                totalMessages: 1,
            },
        }
    );

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

    const res = {
        id: newMessageId,
        chatTag: newMessage.chatTag,
        type: insertMessage.type,
        content: insertMessage.content,
        senderId: insertMessage.senderId,
        senderName: newMessage.senderName,
        senderAvatar: newMessage.senderAvatar,
        tag: newMessage.tag,
        createdTime: String(insertMessage.createdTime),
    };

    // Notification to partner if they not active
    const isPartnerNotActive = !Static.checkIncludeUserId(partnerId);
    if (isPartnerNotActive) {
        Notification.message({
            senderName: newMessage.groupName,
            message: newMessage.content,
            receiver: partnerId,
            chatTagId: newMessage.chatTag,
        });
    }

    return res;
};
