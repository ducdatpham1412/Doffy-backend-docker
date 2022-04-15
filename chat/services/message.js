import { ObjectId } from "mongodb";
import { MESSAGE_TYPE } from "../enum.js";
import mongoDb from "../mongoDb.js";
import Notification from "../notification.js";
import Static from "../static.js";
import { getDateTimeNow, createLinkImage } from "./assistant.js";

export const handleSendMessage = async (newMessage) => {
    const newMessageId = ObjectId();

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

    const setUpdate = {};
    newMessage.listUser.forEach((userId) => {
        if (userId !== insertMessage.senderId) {
            setUpdate[`userSeenMessage.${userId}.istLatest`] = false;
        }
    });

    await mongoDb.collection("chatTag").findOneAndUpdate(
        {
            _id: ObjectId(newMessage.chatTag),
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
            },
            $inc: {
                totalMessages: 1,
            },
        }
    );

    // remake link image
    if (insertMessage.type === MESSAGE_TYPE.image) {
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
