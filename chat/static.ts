import { TypeUserActive } from "./interface/static";

export default class Static {
    static listUserActives: Array<TypeUserActive> = [];
    static listUserInBackground: Array<TypeUserActive> = [];

    static getListUserActives = () => {
        return this.listUserActives;
    };
    static getListUserInBackground = () => {
        return this.listUserInBackground;
    };

    static addUserActive = (params: TypeUserActive) => {
        this.listUserActives.push(params);
    };

    // check include
    static checkIncludeUserId = (userId: number) => {
        const check = this.listUserActives.findIndex(
            (item) => item.userId === userId
        );
        return check >= 0;
    };

    // active user
    static removeUserActive = (socketId: string) => {
        this.listUserActives = this.listUserActives.filter(
            (item) => item.socketId !== socketId
        );
        this.listUserInBackground = this.listUserInBackground.filter(
            (item) => item.socketId !== socketId
        );
    };

    // switch between background and active
    static putInBackground = (socketId: string) => {
        const index = this.listUserActives.findIndex(
            (item) => item.socketId === socketId
        );
        if (index >= 0) {
            this.listUserInBackground.push(this.listUserActives[index]);
            this.listUserActives.splice(index, 1);
        }
    };
    static putBackActive = (socketId: string) => {
        const index = this.listUserInBackground.findIndex(
            (item) => item.socketId === socketId
        );
        if (index >= 0) {
            this.listUserActives.push(this.listUserInBackground[index]);
            this.listUserInBackground.splice(index, 1);
        }
    };
}
