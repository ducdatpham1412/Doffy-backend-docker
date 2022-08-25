import axios from "axios";
import { TYPE_NOTIFICATION } from "./enum";
import env from "./env";
import {
    TypeMessageParams,
    TypeNotificationComment,
} from "./interface/notification";

const requestOneSignal = axios.create({
    baseURL: "https://onesignal.com",
    timeout: 5000,
    headers: {
        "Content-Type": "application/json; charset=utf-8",
        Authorization: `Basic ${env.ONESIGNAL_API_KEY}`,
    },
});

interface ParamsSendNotification {
    contents: {
        en?: string;
        vi?: string;
    };
    headings: {
        en?: string;
        vi?: string;
    };
    filters: Array<{
        field: string;
        key: string;
        relation: "=" | ">" | "<" | ">=" | "<=";
        value: string;
    }>;
    data: {
        type: number;
        [key: string]: any;
    };
}

const sendNotification = async (body: ParamsSendNotification) => {
    return requestOneSignal.post("/api/v1/notifications", {
        app_id: env.ONESIGNAL_APP_ID,
        ...body,
    });
};

export default class Notification {
    static message = async (params: TypeMessageParams) => {
        const { creatorName, message, receiver, conversationId } = params;
        const notificationContents =
            typeof message === "object"
                ? {
                      en: "Send image",
                      vi: "Gửi hình ảnh",
                  }
                : {
                      en: message,
                      vi: message,
                  };
        try {
            await sendNotification({
                contents: notificationContents,
                headings: { en: creatorName },
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
                    conversationId,
                },
            });
        } catch (err) {
            console.log("err when notification message: ", err);
        }
    };

    static comment = async (params: TypeNotificationComment) => {
        const { title, content, receiver, postId } = params;
        try {
            await sendNotification({
                contents: {
                    vi: content.vi,
                    en: content.en,
                },
                headings: {
                    vi: title.vi,
                    en: title.en,
                },
                filters: [
                    {
                        field: "tag",
                        key: "userId",
                        relation: "=",
                        value: String(receiver),
                    },
                ],
                data: {
                    type: TYPE_NOTIFICATION.comment,
                    bubbleId: postId,
                },
            });
        } catch (err) {
            console.log("Err while notification comment: ", err);
        }
    };
}
