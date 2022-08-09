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
