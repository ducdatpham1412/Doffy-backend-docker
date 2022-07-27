export interface TypeMessageParams {
    senderName: string;
    message: string | Array<string>;
    receiver: number;
    chatTagId: string;
}

export interface TypeStartNewChatTagParams {
    message: string;
    receiver: number;
    chatTagId: string;
}
