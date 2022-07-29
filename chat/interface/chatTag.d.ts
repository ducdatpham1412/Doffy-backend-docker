export interface TypeParamStartNewChatTag {
    token: string;
    newChatTag: {
        type: number;
        content: string;
        listUser: Array<number>;
        color: number;
        senderId: number;
        nameBubble?: string;
        idBubble?: string;
    };
}

export interface TypeGetListInfoUserRequest {
    listUserId: Array<number>;
    displayAvatar: boolean;
    token: string;
}
export interface TypeGetListInfoUserResponse {
    id: number;
    name: string;
    avatar: string;
    gender: number;
}

export interface TypeHandleSeenMessage {
    myId: number;
    conversationId: string;
}

export interface TypeAgreePublicChatParams {
    token: string;
    chatTagId: string;
}
