import { createServer } from "http";
import { Server } from "socket.io";
import { SOCKET_EVENT } from "./enum.js";
import mongoDb from "./mongoDb.js";
import {
  changeGroupName,
  getLatestMessage,
  getListSocketIdOfUserEnjoy,
  getMyListChatTagsAndMyId,
  getSocketIdOfListUserActive,
  handleAgreePublicChat,
  handleRequestPublicChat,
  handleSendMessageEnjoy,
  handleStartNewChatTag,
  handleStartNewChatTagEnjoy,
  handleSendMessage,
  increaseAndGetNumberBubbles,
} from "./services.js";
import Static from "./static.js";

const httpServer = createServer();
const io = new Server(httpServer, {
  pingTimeout: 2000,
  pingInterval: 500,
});

const enjoyModeRoom = "enjoy-mode-room";

io.on("connection", (socket) => {
  console.log("\n\nSocket connect with: ", socket.id);

  /**
   * Authenticate
   */
  socket.on(SOCKET_EVENT.authenticate, async (params) => {
    // user have account
    if (params?.token) {
      try {
        const { listMyChatTag, myId } = await getMyListChatTagsAndMyId(
          params.token
        );
        // save to user active
        await mongoDb.collection("userActive").deleteMany({ userId: myId });
        await mongoDb.collection("userActive").insertOne({
          userId: myId,
          socketId: socket.id,
        });
        Static.addUserActive({
          userId: myId,
          socketId: socket.id,
        });
        // join all room of chat tag have in
        listMyChatTag.forEach((item) => {
          socket.join(String(item._id));
        });
      } catch (err) {
        socket.emit(SOCKET_EVENT.unauthorized);
      }
    }

    // use enjoy mode
    else if (params?.myId) {
      await mongoDb
        .collection("userActive")
        .deleteMany({ userId: params.myId });
      await mongoDb.collection("userActive").insertOne({
        userId: params.myId,
        socketId: socket.id,
      });
      Static.addUserActive({
        userId: params.myId,
        socketId: socket.id,
      });
      // join room for only enjoy user
      socket.join(enjoyModeRoom);
    }
  });

  /**
   * Bubble
   */
  socket.on(SOCKET_EVENT.createBubble, async ({ myId, bubble }) => {
    const idOfNewBubble = await increaseAndGetNumberBubbles();
    const newBubble = {
      id: idOfNewBubble,
      name: bubble.name,
      icon: bubble.icon,
      color: bubble.idHobby,
      description: bubble.description,
      creatorId: myId,
      creatorAvatar: bubble.privateAvatar,
    };
    // user enjoy - only send to other user enjoy
    if (String(myId).includes("__")) {
      // const listSocketEnjoy = await getListSocketIdOfUserEnjoy();
      // listSocketEnjoy.forEach((item) => {
      //   io.to(item).emit(SOCKET_EVENT.createBubble, newBubble);
      // });
      io.to(enjoyModeRoom).emit(SOCKET_EVENT.createBubble, newBubble);
    }
    // user have account - send to all
    else {
      io.emit(SOCKET_EVENT.createBubble, newBubble);
    }
  });

  /**
   * ChatTag
   */
  socket.on(SOCKET_EVENT.createChatTag, async (params) => {
    // user have account
    if (params?.token) {
      const res = await handleStartNewChatTag(params);
      // send socket message to existed chat tag
      if (res.isChatTagExisted) {
        io.to(res.response.chatTag).emit(SOCKET_EVENT.message, res.response);
        return;
      }

      // send socket delete bubble
      if (params.newChatTag?.idBubble) {
        io.emit(SOCKET_EVENT.deleteBubble, params.newChatTag?.idBubble);
      }

      // send new chat tag to all member in chat
      const listSocketId = await getSocketIdOfListUserActive(
        res.response.listUser.map((item) => item.id)
      );
      listSocketId.forEach((socketId) => {
        io.to(socketId).emit(SOCKET_EVENT.createChatTag, res.response);
      });
    }

    // user enjoy mode
    else if (params?.myId) {
      const res = handleStartNewChatTagEnjoy(params);

      // send socket delete bubble
      const listSocketEnjoy = await getListSocketIdOfUserEnjoy();
      listSocketEnjoy.forEach((socketId) => {
        io.to(socketId).emit(
          SOCKET_EVENT.deleteBubble,
          params.newChatTag?.idBubble
        );
      });

      // send new chat tag to all member in chat
      const listSocketId = await getSocketIdOfListUserActive(
        res.newChatTag.listUser.map((item) => item.id)
      );
      listSocketId.forEach((socketId) => {
        io.to(socketId).emit(SOCKET_EVENT.createChatTag, res);
      });
    }
  });
  // after receive socket "createChatTag" in client, join room of that chat tag
  socket.on(SOCKET_EVENT.joinRoom, (chatTagId) => {
    console.log("join room: ", chatTagId);
    socket.join(chatTagId);
  });

  socket.on(SOCKET_EVENT.seenMessage, async (params) => {
    let res = undefined;
    // enjoy mode
    if (params?.isEnjoy) {
      res = {
        chatTagId: params.chatTagId,
        userSeen: params.myId,
      };
    }
    // user have account
    else {
      res = await getLatestMessage(params);
    }
    io.to(params.chatTagId).emit(SOCKET_EVENT.seenMessage, res);
  });

  socket.on(SOCKET_EVENT.requestPublicChat, async (chatTagId) => {
    await handleRequestPublicChat(chatTagId);
    io.to(chatTagId).emit(SOCKET_EVENT.requestPublicChat, chatTagId);
  });
  socket.on(SOCKET_EVENT.agreePublicChat, async (params) => {
    const chatTagPublic = await handleAgreePublicChat(params);
    if (chatTagPublic) {
      io.to(chatTagPublic.id).emit(
        SOCKET_EVENT.allAgreePublicChat,
        chatTagPublic
      );
    }
  });

  socket.on(SOCKET_EVENT.changeGroupName, async (params) => {
    await changeGroupName(params);
    io.to(params.chatTagId).emit(SOCKET_EVENT.changeGroupName, {
      chatTagId: params.chatTagId,
      newName: params.newName,
    });
  });

  /**
   * Block, stop conversation
   */
  socket.on(SOCKET_EVENT.isBlocked, async ({ listUserId, listChatTagId }) => {
    const listSocketId = await getSocketIdOfListUserActive(listUserId);
    listSocketId.forEach((item) => {
      io.to(item).emit(SOCKET_EVENT.isBlocked, listChatTagId);
    });
  });
  socket.on(SOCKET_EVENT.unBlocked, async ({ listUserId, listChatTagId }) => {
    const listSocketId = await getSocketIdOfListUserActive(listUserId);
    listSocketId.forEach((item) => {
      io.to(item).emit(SOCKET_EVENT.unBlocked, listChatTagId);
    });
  });

  socket.on(SOCKET_EVENT.stopConversation, (chatTagId) => {
    io.to(chatTagId).emit(SOCKET_EVENT.stopConversation, chatTagId);
  });
  socket.on(SOCKET_EVENT.openConversation, (chatTagId) => {
    io.to(chatTagId).emit(SOCKET_EVENT.openConversation, chatTagId);
  });

  /**
   * Message
   */
  socket.on(SOCKET_EVENT.message, async (params) => {
    const res = await handleSendMessage(params);
    io.to(res.chatTag).emit(SOCKET_EVENT.message, res);
  });
  socket.on(SOCKET_EVENT.messageEnjoy, (params) => {
    const res = handleSendMessageEnjoy(params);
    io.to(res.chatTag).emit(SOCKET_EVENT.messageEnjoy, res);
  });

  /**
   * Disconnect
   */
  socket.on("disconnect", async (reason) => {
    console.log(`Disconnected: ${socket.id}\nReason: `, reason);

    await mongoDb
      .collection("userActive")
      .findOneAndDelete({ socketId: socket.id });
    /**
     * Leave room - you don't need because socketIO will do this for you
     */
    Static.removeUserActive(socket.id);
  });
});

httpServer.listen(3000);
