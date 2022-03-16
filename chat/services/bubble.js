import mongoDb from "../mongoDb.js";

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
