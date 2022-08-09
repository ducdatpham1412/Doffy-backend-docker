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

export interface TypeCreateChatTag {
    token: string;
    conversation: {
        content: string;
        userId: number;
    };
}

export interface TypeChatTagResponse {
    id: string;
    listUser: Array<TypeMemberInListChatTag>;
    conversationName: string;
    conversationImage: string;
    userData: {
        [key: string]: {
            created: string;
            modified: string;
        };
    };
    color: number;
    modified: string;
    status: number;
    isBlocked: boolean;
    latestMessage: string;
    // in front-end
    userTyping?: Array<number>;
}
