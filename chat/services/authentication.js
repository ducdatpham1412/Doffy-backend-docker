import { request } from "../request.js";
import mongoDb from "../mongoDb.js";

export const getMyListChatTagsAndMyId = async (token) => {
    const res = await request.get("/auth/verify-token", {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
    const myId = res.data;
    const listMyChatTag = await mongoDb
        .collection("chatTag")
        .find({
            listUser: myId,
        })
        .toArray();
    return { listMyChatTag, myId };
};
