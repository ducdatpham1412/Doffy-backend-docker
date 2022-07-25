export interface TypeSendMessageRequest {
    chatTag: string;
    groupName: string;
    type: number;
    content: string | Array<string>;
    senderId: number;
    senderName: string;
    senderAvatar: string;
    listUser: Array<number>;
    tag: string;
}
