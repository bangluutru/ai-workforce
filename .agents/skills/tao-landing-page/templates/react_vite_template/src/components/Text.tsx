import React from 'react';

const FLAG = /(\[CẦN XÁC MINH[^\]]*\])/g;

/** Hiển thị chuỗi nội dung; đoạn [CẦN XÁC MINH: ...] được tô nổi bật để không bị xuất bản nhầm. */
export const Text: React.FC<{ value?: string }> = ({ value }) => {
  if (!value) return null;
  const parts = value.split(FLAG);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith('[CẦN XÁC MINH') ? (
          <mark key={i} className="verify-flag">{p}</mark>
        ) : (
          <React.Fragment key={i}>{p}</React.Fragment>
        )
      )}
    </>
  );
};
