import { MongoClient } from "mongodb";

const uri = `mongodb://username:password@127.0.0.1:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=2000&appname=MongoDB%20Compass&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

const query = async () => {
    // update again total likes
    const allPosts = await mongoDb
        .collection("discovery_post")
        .find({}, { session: client.startSession() })
        .toArray();
    allPosts.forEach(async (post) => {
        const totalReacts = await mongoDb.collection("reaction").count({
            type: 0,
            reacted_id: String(post._id),
            status: 1,
        });
        await mongoDb.collection("discovery_post").updateOne(
            {
                _id: post._id,
            },
            {
                $set: {
                    total_reacts: totalReacts,
                },
            }
        );
    });

    // set total likes to collection total_items
    const totalUsers = 33; // edit this in production
    for (let i = 1; i <= totalUsers; i++) {
        const allPosts = await mongoDb
            .collection("discovery_post")
            .find({
                creator: i,
                status: 1,
            })
            .toArray();
        let totalLikes = 0;
        allPosts.forEach((post) => {
            totalLikes += post.total_reacts;
        });
        await mongoDb.collection("total_items").insertOne({
            type: 2,
            user_id: i,
            value: totalLikes,
        });
    }
};

query();
