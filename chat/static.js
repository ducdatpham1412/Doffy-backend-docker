export default class Static {
  static listUserActives = [];

  static getListUserActives = () => {
    return this.listUserActives;
  };

  static addUserActive = (params) => {
    this.listUserActives.push(params);
  };

  static checkIncludeUserId = (userId) => {
    const check = this.listUserActives.findIndex(
      (item) => item.userId === userId
    );
    return check > 0;
  };

  static removeUserActive = (socketId) => {
    this.listUserActives = this.listUserActives.filter(
      (item) => item.socketId !== socketId
    );
  };
}
