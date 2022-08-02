export interface TypeSendMessageRequest {
    conversationId: string;
    type: number;
    content: string | Array<string>;
    creator: number;
    creatorName: string;
    creatorAvatar: string;
    tag: string;
}

export interface TypeSendMessageResponse {
    id: string;
    conversationId: string;
    type: number;
    content: string | Array<string>;
    creator: number;
    creatorName: string;
    creatorAvatar: string;
    created: string;
    tag?: string | undefined;
}

export interface TypeTyping {
    conversationId: string;
    userId: string;
}
