import { request } from "../request";
import mongoDb from "../mongoDb";

export const getMyListChatTagsAndMyId = async (token: string) => {
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
