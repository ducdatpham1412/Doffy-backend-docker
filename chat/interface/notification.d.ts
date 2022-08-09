export interface TypeMessageParams {
    creatorName: string;
    message: string | Array<string>;
    receiver: number;
    conversationId: string;
}

export interface TypeNotificationComment {
    title: {
        vi: string;
        en: string;
    };
    content: {
        vi: string;
        en: string;
    };
    receiver: number;
    postId: string;
}
