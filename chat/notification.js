import axios from "axios";
import { TYPE_NOTIFICATION } from "./enum.js";
import env from "./env.js";

const requestOneSignal = axios.create({
  baseURL: "https://onesignal.com",
  timeout: 5000,
  headers: {
    "Content-Type": "application/json; charset=utf-8",
    Authorization: `Basic ${env.ONESIGNAL_API_KEY}`,
  },
});

const sendNotification = async (body) => {
  return requestOneSignal.post("/api/v1/notifications", {
    app_id: env.ONESIGNAL_APP_ID,
    ...body,
  });
};

export default class Notification {
  static message = async (params) => {
    const { senderName, message, receiver, chatTagId } = params;
    try {
      await sendNotification({
        contents: { en: message },
        headings: { en: senderName },
        filters: [
          {
            field: "tag",
            key: "userId",
            relation: "=",
            value: String(receiver),
          },
          // { operator: "OR" },
          // { field: "amount_spent", relation: ">", value: "0" },
        ],
        // included_segments: ["Subscribed Users"],
        data: {
          type: TYPE_NOTIFICATION.message,
          chatTagId,
        },
      });
    } catch (err) {
      console.log("err when notification message: ", err);
    }
  };

  static startNewChatTag = async (params) => {
    const { message, receiver } = params;
    try {
      await sendNotification({
        contents: { en: message },
        headings: { en: "Một người lạ làm quen với bạn 😇" },
        filters: [
          {
            field: "tag",
            key: "userId",
            relation: "=",
            value: String(receiver),
          },
        ],
        data: {
          type: TYPE_NOTIFICATION.newChatTag,
        },
      });
    } catch (err) {
      console.log("err when notification start chat tag: ", err);
    }
  };

  static follow = async (params) => {
    const { followerName, receiver } = params;
    try {
      await sendNotification({
        contents: `${followerName} bắt đầu theo dõi bạn`,
        filters: [
          {
            field: "tag",
            key: "userId",
            relation: "=",
            value: String(receiver),
          },
        ],
        data: {
          type: TYPE_NOTIFICATION.follow,
        },
      });
    } catch (err) {
      console.log("err when notification follow: ", err);
    }
  };
}
