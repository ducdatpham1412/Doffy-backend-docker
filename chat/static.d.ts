interface TypeUserActive {
  userId: number | string;
  socketId: string;
}

export default class Static {
  private static listUserActives: Array<TypeUserActive>;

  static addUserActive(params: TypeUserActive): void;

  static checkIncludeUserId(userId: string | number): boolean;

  static removeUserActive(socketId: string): void;
}
