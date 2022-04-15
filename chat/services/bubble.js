import { ObjectId } from "mongodb";
import { CHAT_TAG } from "../enum.js";
import mongoDb from "../mongoDb.js";
import { request } from "../request.js";
import { getUserIdFromToken } from "./assistant.js";

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
            },
            $set: {
                [`userSeenMessage.${myId}`]: {
                    latestMessage: "",
                    isLatest: false,
                },
            },
        }
    );

    if (!chatTag.value) {
        throw new Error("ChatTag not found");
    }

    return group.value.chatTagId;
};
