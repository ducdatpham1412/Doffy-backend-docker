export default class Static {
  static listUserActives = [];
  static listUserInBackground = [];

  static getListUserActives = () => {
    return this.listUserActives;
  };
  static getListUserInBackground = () => {
    return this.listUserInBackground;
  };

  static addUserActive = (params) => {
    this.listUserActives.push(params);
  };

  // check include
  static checkIncludeUserId = (userId) => {
    const check = this.listUserActives.findIndex(
      (item) => item.userId === userId
    );
    return check >= 0;
  };

  // active user
  static removeUserActive = (socketId) => {
    this.listUserActives = this.listUserActives.filter(
      (item) => item.socketId !== socketId
    );
    this.listUserInBackground = this.listUserInBackground.filter(
      (item) => item.socketId !== socketId
    );
  };

  // switch between background and active
  static putInBackground = (socketId) => {
    const index = this.listUserActives.findIndex(
      (item) => item.socketId === socketId
    );
    if (index >= 0) {
      this.listUserInBackground.push(this.listUserActives[index]);
      this.listUserActives.splice(index, 1);
    }
  };
  static putBackActive = (socketId) => {
    const index = this.listUserInBackground.findIndex(
      (item) => item.socketId === socketId
    );
    if (index >= 0) {
      this.listUserActives.push(this.listUserInBackground[index]);
      this.listUserInBackground.splice(index, 1);
    }
  };

  // get user id from their socket id
  static getUserIdFromSocketId = (socketId) => {
    return this.listUserActives.find((item) => item.socketId === socketId)
      ?.userId;
  };
}
