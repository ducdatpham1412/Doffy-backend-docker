interface TypeMessage {
  senderName: string;
  message: string;
  receiver: number;
  chatTagId: string;
}

interface TypeStartNewChatTag {
  message: string;
  receiver: number;
}

interface TypeFollow {
  followerName: string;
  receiver: number;
}

export default class Notification {
  static message(params: TypeMessage): Promise<void>;

  static startNewChatTag(params: TypeStartNewChatTag): Promise<void>;

  static follow(params: TypeFollow): Promise<void>;
}
