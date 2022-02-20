interface TypeMessage {
  senderName: string;
  message: string;
  receiver: number;
  chatTagId: string;
}

interface TypeStartNewChatTag {
  message: string;
  receiver: number;
  chatTagId: string;
}

export default class Notification {
  static message(params: TypeMessage): Promise<void>;

  static startNewChatTag(params: TypeStartNewChatTag): Promise<void>;
}
