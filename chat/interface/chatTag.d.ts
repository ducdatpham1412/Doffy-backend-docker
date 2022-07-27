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

export interface TypeParamsGetLatestMessage {
    myId: number;
    chatTagId: string;
}

export interface TypeChangeGroupNameParams {
    token: string;
    chatTagId: string;
    newName: string;
}

export interface TypeChangeColorParams {
    token: string;
    newColor: number;
    chatTagId: string;
    socketId: string;
}

export interface TypeAgreePublicChatParams {
    token: string;
    chatTagId: string;
}
