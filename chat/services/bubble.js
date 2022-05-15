import { ObjectId } from "mongodb";
import { CHAT_TAG, MESSAGE_TYPE } from "../enum.js";
import mongoDb from "../mongoDb.js";
import { request } from "../request.js";
import { getDateTimeNow, getUserIdFromToken } from "./assistant.js";

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

export const addComment = async (params) => {
    const { token, bubbleId, content, commentReplied } = params;

    const res = await request.post(
        `/common/add-comment/${bubbleId}`,
        {
            content,
            commentReplied,
        },
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
    );

    return res;
};

export const joinCommunity = async (params) => {
    const { token, profilePostGroupId } = params;

    const myId = await getUserIdFromToken(token);

    // Add new member is profilePostGroup
    const group = await mongoDb.collection("profilePostGroup").findOneAndUpdate(
        {
            _id: ObjectId(profilePostGroupId),
            listMembers: {
                $ne: myId,
            },
        },
        {
            $push: {
                listMembers: myId,
            },
        }
    );
    if (!group.value) {
        throw new Error("Joined this group");
    }

    // Update in list chat tag
    const timeNow = getDateTimeNow();
    const insertMessage = {
        _id: ObjectId(),
        type: MESSAGE_TYPE.joinCommunity,
        content: "",
        senderId: myId,
        createdTime: timeNow,
    };
    const chatTag = await mongoDb.collection("chatTag").findOneAndUpdate(
        {
            _id: ObjectId(group.value.chatTagId),
            type: CHAT_TAG.group,
            listUser: {
                $ne: myId,
            },
        },
        {
            $push: {
                listUser: myId,
                listMessages: {
                    $each: [insertMessage],
                    $position: 0,
                },
            },
            $set: {
                [`userSeenMessage.${myId}`]: {
                    latestMessage: "",
                    isLatest: false,
                },
                updateTime: timeNow,
            },
            $inc: {
                totalMessages: 1,
            },
        }
    );
    if (!chatTag.value) {
        throw new Error("ChatTag not found");
    }

    // Set isLatest status of all member is chat tag
    const setUpdate = {};
    chatTag.value.listUser.forEach((userId) => {
        setUpdate[`userSeenMessage.${userId}.isLatest`] = false;
    });
    await mongoDb.collection("chatTag").findOneAndUpdate(
        {
            _id: ObjectId(group.value.chatTagId),
        },
        {
            $set: setUpdate,
        }
    );

    return group.value.chatTagId;
};
