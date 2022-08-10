import { Document, ObjectId, PullOperator } from "mongodb";
import { CHAT_TAG, MESSAGE_TYPE, STATUS } from "../enum";
import { TypeAddComment, TypeParamsJoinCommunity } from "../interface/bubble";
import { TypeNotificationComment } from "../interface/notification";
import mongoDb from "../mongoDb";
import Notification from "../notification";
import { getDateTimeNow, getUserIdFromToken } from "./assistant";

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

export const addComment = async (params: TypeAddComment) => {
    const { token, comment } = params;
    const myId = await getUserIdFromToken(token);
    const now = getDateTimeNow();

    const insert_comment = {
        _id: new ObjectId(),
        post_id: comment.postId,
        replied_id: comment?.commentReplied || null,
        content: comment.content,
        images: [],
        creator: myId,
        created: now,
        modified: now,
        status: STATUS.active,
    };
    await mongoDb.collection("discovery_comment").insertOne(insert_comment);

    // Do insert collection "notification" later
    const insert_notification = {};

    // Notification OneSignal
    const post = await mongoDb.collection("discovery_post").findOne({
        _id: new ObjectId(comment.postId),
    });
    if (post) {
        const dataNotification: TypeNotificationComment = {
            title: {
                vi: `${comment.creatorName} đã bình luận`,
                en: `${comment.creatorName} commented`,
            },
            content: {
                vi: comment.content,
                en: comment.content,
            },
            receiver: post.creator,
            postId: comment.postId,
        };
        Notification.comment(dataNotification);
    }

    // Socket send back front-end
    const socketNotification = {
        commentReplied: comment.commentReplied,
        data: {
            id: String(insert_comment._id),
            content: insert_comment.content,
            numberLikes: 0,
            isLiked: false,
            creator: insert_comment.creator,
            creatorName: comment.creatorName,
            creatorAvatar: comment.creatorAvatar,
            created: String(now),
        },
    };
    return socketNotification;
};

export const joinCommunity = async (params: TypeParamsJoinCommunity) => {
    const { token, profilePostGroupId } = params;

    const myId = await getUserIdFromToken(token);

    // Add new member is profilePostGroup
    const group = await mongoDb.collection("profilePostGroup").findOneAndUpdate(
        {
            _id: new ObjectId(profilePostGroupId),
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
        _id: new ObjectId(),
        type: MESSAGE_TYPE.joinCommunity,
        content: "",
        senderId: myId,
        createdTime: timeNow,
    };
    const chatTag = await mongoDb.collection("chatTag").findOneAndUpdate(
        {
            _id: new ObjectId(group.value.chatTagId),
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
            } as unknown as PullOperator<Document>,
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
    const setUpdate: any = {};
    chatTag.value.listUser.forEach((userId: any) => {
        setUpdate[`userSeenMessage.${userId}.isLatest`] = false;
    });
    await mongoDb.collection("chatTag").findOneAndUpdate(
        {
            _id: new ObjectId(group.value.chatTagId),
        },
        {
            $set: setUpdate,
        }
    );

    return group.value.chatTagId;
};
