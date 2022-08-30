import { Document, ObjectId, PullOperator } from "mongodb";
import {
    CHAT_TAG,
    MESSAGE_TYPE,
    NOTIFICATION_STATUS,
    STATUS,
    TYPE_NOTIFICATION,
} from "../enum";
import {
    TypeAddComment,
    TypeInsertNotification,
    TypeNotificationResponse,
    TypeParamsJoinCommunity,
} from "../interface/bubble";
import { TypeNotificationComment } from "../interface/notification";
import mongoDb from "../mongoDb";
import Notification from "../notification";
import {
    createLinkImage,
    getDateTimeNow,
    getSocketIdOfUserId,
    getUserIdFromToken,
} from "./assistant";

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

    const post = await mongoDb.collection("discovery_post").findOneAndUpdate(
        {
            _id: new ObjectId(comment.postId),
        },
        {
            $inc: {
                total_comments: 1,
            },
        }
    );

    // Do insert collection "notification" later
    let socketNotification;
    if (post.value?.creator) {
        const insertNotification: TypeInsertNotification = {
            _id: new ObjectId(),
            type: TYPE_NOTIFICATION.comment,
            user_id: post.value.creator,
            post_id: String(post.value?._id),
            creator: myId,
            created: getDateTimeNow(),
            status: NOTIFICATION_STATUS.notRead,
        };
        await mongoDb.collection("notification").insertOne(insertNotification);

        const receiverSocketId = await getSocketIdOfUserId(post.value.creator);
        if (receiverSocketId) {
            const temp: TypeNotificationResponse = {
                id: String(insertNotification._id),
                type: insertNotification.type,
                image: post.value?.images[0]
                    ? createLinkImage(post.value?.images[0])
                    : "",
                postId: String(post.value._id),
                creator: myId,
                creatorName: comment.creatorName,
                creatorAvatar: comment.creatorAvatar,
                created: String(insertNotification.created),
                isRead: false,
            };
            socketNotification = {
                receiverSocketId: receiverSocketId,
                data: temp,
            };
        }
    }

    // One signal
    if (post.value) {
        const dataNotification: TypeNotificationComment = {
            title: {
                vi: `${comment.creatorName} đã bình luận`,
                en: `${comment.creatorName} commented`,
            },
            content: {
                vi: comment.content,
                en: comment.content,
            },
            receiver: post.value.creator,
            postId: comment.postId,
        };
        Notification.comment(dataNotification);
    }

    // Socket send back front-end
    const socketComment = {
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
    return {
        socketComment,
        socketNotification,
    };
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
