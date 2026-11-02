'use strict';
/* PHÂN ĐOẠN 01 — [tên] · mẫu cho seq-XX.js (copy, đổi số, giữ cấu trúc)
   ĐỌC continuity.md TRƯỚC: trạng thái nhân vật/đạo cụ/ánh sáng ở cuối phân đoạn trước = điểm bắt đầu ở đây.
   BEAT SHEET
   shot        dur   khán giả chú ý gì          camera                 âm thanh
   wide        4.0   thiết lập thế giới          wide, pan chậm          motif mở
   medium      4.0   nhân vật bắt đầu hành trình push-in                 motif
   KẾT PHÂN ĐOẠN (ghi vào continuity.md): vị trí heroX(T), hướng màn hình, đạo cụ đang cầm, biểu cảm, giờ trong ngày. */

addShot('01', 'wide', 4.0, (c, T, tau) => {
  const v = shotCam(tau, [[0, heroX(T) - 80, 60, .85], [4, heroX(T) + 40, 60, .9]], 2);
  drawWorld(c, T, v); applyView(c, v); drawHero(c, T);
});

addShot('01', 'medium', 4.0, (c, T, tau) => {
  const v = shotCam(tau, [[0, heroX(T) + 20, 120, 1.25], [4, heroX(T) + 30, 110, 1.35]], 2.5);
  drawWorld(c, T, v); applyView(c, v); drawHero(c, T);
});
