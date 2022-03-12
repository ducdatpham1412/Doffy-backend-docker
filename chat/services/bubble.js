import { ObjectId } from "mongodb";
import mongoDb from "../mongoDb.js";

export const handleCreateBubble = async ({ myId, bubble }) => {
    const newBubble = {
        name: bubble.name,
        icon: bubble.icon,
        color: bubble.idHobby,
        description: bubble.description,
        creatorId: myId,
        creatorAvatar: bubble.privateAvatar,
    };
    if (!String(myId).includes("__")) {
        await mongoDb.collection("bubblePalaceActive").insertOne(newBubble);
    }
    await mongoDb.collection("numberBubbles").findOneAndUpdate(
        {},
        {
            $inc: {
                number: 1,
            },
        }
    );

    return {
        id: String(newBubble._id || ObjectId()),
        ...newBubble,
    };
};

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
