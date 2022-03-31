import mongoDb from "../mongoDb.js";
import { request } from "../request.js";

export const getListSocketIdOfUserEnjoy = async () => {
    const res = await mongoDb
        .collection("userActive")
        .find({
            userId: {
                $regex: "__",
            },
        })
        .toArray();
    return res.map((item) => item.socketId);
};

export const addComment = async (params) => {
    const { token, bubbleId, content, commentReplied } = params;

    const res = await request.post(
        `/common/add-comment/${bubbleId}`,
        {
            content,
            commentReplied,
        },
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        }
    );

    return res;
};
