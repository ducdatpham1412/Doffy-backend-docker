import { request } from "../request";
import mongoDb from "../mongoDb";

export const getMyListChatTagsAndMyId = async (token: string) => {
    const res = await request.get("/auth/verify-token", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
    const myId = res.data;
    const listMyConversations = await mongoDb
        .collection("chat_conversation")
        .find({
            list_users: myId,
        })
        .toArray();
    return { listMyConversations, myId };
};
