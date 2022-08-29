import { ObjectId } from "mongodb";

export interface TypeAddComment {
    token: string;
    comment: {
        postId: string;
        commentReplied: string | null;
        content: string;
        images: Array<string>;
        creatorName: string;
        creatorAvatar: string;
    };
}

export interface TypeParamsJoinCommunity {
    token: string;
    profilePostGroupId: string;
}

export interface TypeInsertNotification {
    _id: ObjectId;
    type: number;
    user_id: number;
    post_id?: string;
    creator: number;
    created: Date;
    status: number;
}

export interface TypeNotificationResponse {
    id: string;
    type: number;
    image?: string;
    postId?: string;
    creator: number;
    creatorName: string;
    creatorAvatar: string;
    created: string;
    isRead: boolean;
}
