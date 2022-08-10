import { MongoClient, ObjectId } from "mongodb";

const uri = `mongodb://ducdatpham:ducdat123@127.0.0.1:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=2000&appname=MongoDB%20Compass&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

const query = async () => {
    const oldListProfilePost = await mongoDb
        .collection("__old_profile_post")
        .find()
        .toArray();
    oldListProfilePost.forEach(async (post) => {
        const newPost = {
            _id: post._id,
            topic: 0, // 0 is topic travel
            feeling: null,
            location: null,
            content: post.content,
            images: post.images,
            stars: 5,
            link: null,
            total_reacts: post.peopleLike.length,
            total_comments: post.listComments.length,
            creator: post.creatorId,
            created: post.createdTime,
            modified: post.createdTime,
            status: 1, // 1 is status active
        };
        await mongoDb.collection("discovery_post").insertOne(newPost);

        // Comments
        post.listComments.forEach(async (comment: any) => {
            const newComment = {
                _id: new ObjectId(comment.id),
                post_id: String(newPost._id),
                replied_id: null,
                content: comment.content,
                images: [],
                creator: comment.creatorId,
                created: new Date(comment.createdTime),
                modified: new Date(comment.createdTime),
                status: 1,
            };
            await mongoDb.collection("discovery_comment").insertOne(newComment);
            if (comment.listCommentsReply.length) {
                comment.listCommentsReply.forEach(async (commentReply: any) => {
                    const newCommentReply = {
                        _id: new ObjectId(commentReply.id),
                        post_id: String(newPost._id),
                        replied_id: String(newComment._id),
                        content: commentReply.content,
                        images: [],
                        creator: commentReply.creatorId,
                        created: new Date(commentReply.createdTime),
                        modified: new Date(commentReply.createdTime),
                        status: 1,
                    };
                    await mongoDb
                        .collection("discovery_comment")
                        .insertOne(newCommentReply);
                });
            }
        });

        // Reaction
        post.peopleLike.forEach(async (reaction: any) => {
            const newReaction = {
                type: 0, // 0 is type react post
                reacted_id: String(newPost._id),
                creator: reaction.id,
                created: reaction.createdTime,
                status: 1,
            };
            await mongoDb.collection("reaction").insertOne(newReaction);
        });
    });
};

query();
