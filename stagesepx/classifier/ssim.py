from loguru import logger
import typing
import cv2

from stagesepx.classifier.base import BaseClassifier, ClassifierResult
from stagesepx import toolbox


class SSIMClassifier(BaseClassifier):
    def classify(self, video_path: str, threshold: float = None) -> typing.List[ClassifierResult]:
        logger.debug(f'classify with {self.__class__.__name__}')
        assert self.data, 'should load data first'

        if not threshold:
            threshold = 0.85

        final_result: typing.List[ClassifierResult] = list()
        with toolbox.video_capture(video_path) as cap:
            ret, frame = cap.read()
            while ret:
                frame_id = toolbox.get_current_frame_id(cap)
                frame_timestamp = toolbox.get_current_frame_time(cap)
                frame = toolbox.compress_frame(frame)

                result = list()
                for each_stage_name, each_stage_pic_list in self.data.items():
                    each_result = list()
                    for each in each_stage_pic_list:
                        target_pic = cv2.imread(each.as_posix())
                        target_pic = toolbox.compress_frame(target_pic)
                        each_pic_ssim = toolbox.compare_ssim(frame, target_pic)
                        each_result.append(each_pic_ssim)
                    ssim = max(each_result)
                    result.append((each_stage_name, ssim))
                    logger.debug(f'stage [{each_stage_name}]: {ssim}')

                result = max(result, key=lambda x: x[1])
                if result[1] < threshold:
                    logger.debug('not a known stage, set it -1')
                    result = ('-1', result[1])
                logger.debug(f'frame {frame_id} ({frame_timestamp}) belongs to {result[0]}')

                final_result.append(ClassifierResult(video_path, frame_id, frame_timestamp, result[0]))
                ret, frame = cap.read()
        return final_result
