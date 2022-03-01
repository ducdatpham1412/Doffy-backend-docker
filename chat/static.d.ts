interface TypeUserActive {
    userId: number | string;
    socketId: string;
}

export default class Static {
    private static listUserActives: Array<TypeUserActive>;
    private static listUserInBackground: Array<TypeUserActive>;

    static getListUserActives(): Array<TypeUserActive>;
    static getListUserInBackground(): Array<TypeUserActive>;

    static addUserActive(params: TypeUserActive): void;

    static checkIncludeUserId(userId: string | number): boolean;

    static removeUserActive(socketId: string): void;

    static putInBackground(socketId: string): void;
    static putBackActive(socketId: string): void;

    static getUserIdFromSocketId(socketId: string): number | undefined;
}
