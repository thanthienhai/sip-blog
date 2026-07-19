"""Build the Vietnamese Game Theory Foundations Anki deck.

The builder uses an existing two-field Anki package only as an empty schema,
then writes the deck with Python's standard library.  Run this file from any
directory with Python 3 to recreate the .apkg file.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import html
import json
import sqlite3
import tempfile
import time
import zipfile


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT.parent / "datetime" / "SIP-DateTime-Comprehensive.apkg"
OUTPUT = ROOT / "SIP-Game-Theory-Foundations.apkg"

DECK_ID = 1990003001
MODEL_ID = 1783242367233
DECK_NAME = "Lý thuyết trò chơi - Nền tảng"
MODEL_NAME = "Game Theory Foundations"

# question, answer, tag
CARDS = [
    ("Lý thuyết trò chơi nghiên cứu điều gì?",
     "Nghiên cứu các quyết định có tính <b>chiến lược</b>: kết quả của mỗi bên phụ thuộc không chỉ vào lựa chọn của họ mà còn vào lựa chọn của các bên khác.", "overview"),
    ("Muốn mô hình hóa một tình huống bằng Lý thuyết trò chơi, cần xác định 4 yếu tố nào?",
     "<b>Người chơi</b>, <b>chiến lược</b>, <b>kết cục/lợi ích</b> (payoffs) và <b>thông tin</b>.", "core_elements"),
    ("Người chơi (players) là gì? Có thể là những ai?",
     "Là các bên ra quyết định trong trò chơi: cá nhân, doanh nghiệp, quốc gia hoặc agent AI trong một hệ thống máy học.", "core_elements"),
    ("Chiến lược (strategy) là gì?",
     "Là tập hợp mọi phương án/hành động khả thi mà một người chơi có thể chọn trong mọi tình huống có thể xảy ra.", "core_elements"),
    ("Kết cục/lợi ích (payoff) là gì?",
     "Là phần thưởng hoặc hậu quả mà mỗi người chơi nhận sau khi mọi bên đã chọn chiến lược; thường lượng hóa bằng tiền, điểm hoặc độ hữu dụng.", "core_elements"),
    ("Thông tin (information) trong một trò chơi bao gồm gì?",
     "Là kiến thức người chơi có về luật chơi, các hành động trước đó của đối thủ và ma trận lợi ích tại thời điểm ra quyết định.", "core_elements"),
    ("Tính duy lý (rationality) giả định điều gì?",
     "Mỗi người chơi tỉnh táo và tìm cách <b>tối đa hóa lợi ích của chính mình</b>; họ không cố ý chọn phương án tệ hơn khi có phương án tốt hơn.", "assumptions"),
    ("Tri thức chung (common knowledge) là gì?",
     "Mọi người biết luật chơi, payoff của nhau và biết mọi bên là duy lý; đồng thời mỗi bên biết rằng các bên khác cũng biết những điều đó — lặp lại vô hạn.", "assumptions"),
    ("Tính duy lý khác với 'luôn ích kỷ' như thế nào?",
     "Duy lý nghĩa là tối đa hóa <b>hàm lợi ích</b> của mình. Hàm này có thể bao gồm tiền, danh tiếng, công bằng hay lợi ích của người khác; không nhất thiết chỉ là tiền bạc hay ích kỷ.", "assumptions"),
    ("Duy lý giới hạn (bounded rationality) nhắc ta điều gì?",
     "Trong thực tế, con người bị giới hạn bởi thông tin, năng lực tính toán và cảm xúc. Lý thuyết trò chơi hành vi điều chỉnh các giả định cổ điển để gần thực tế hơn.", "assumptions"),
    ("Chiến lược ưu thế (dominant strategy) là gì?",
     "Là chiến lược đem lại payoff tốt hơn (hoặc không kém) mọi lựa chọn khác <b>với bất kỳ</b> chiến lược nào của đối thủ. Nếu có chiến lược ưu thế nghiêm ngặt, người chơi duy lý sẽ chọn nó.", "solution_concepts"),
    ("Khi nào một chiến lược là ưu thế nghiêm ngặt?",
     "Khi nó cho payoff <b>cao hơn</b> mọi chiến lược thay thế trong mọi tình huống đối thủ có thể chọn.", "solution_concepts"),
    ("Chiến lược ưu thế có cần dự đoán đối thủ không?",
     "Không. Vì nó là lựa chọn tốt nhất bất kể đối thủ làm gì; người chơi không cần đoán suy nghĩ hay hành động của đối thủ.", "solution_concepts"),
    ("Cân bằng Nash (Nash equilibrium) là gì?",
     "Là cấu hình chiến lược mà không người chơi nào muốn tự mình đổi chiến lược, vì đổi đơn phương sẽ không làm payoff của họ tốt hơn.", "solution_concepts"),
    ("Điều kiện tương đương của Cân bằng Nash là gì?",
     "Mỗi người chơi đang chọn một <b>phản ứng tốt nhất</b> trước chiến lược hiện tại của các người chơi khác.", "solution_concepts"),
    ("Phân biệt chiến lược ưu thế và Cân bằng Nash.",
     "<b>Chiến lược ưu thế</b> tốt nhất với mọi nước đi của đối thủ. <b>Cân bằng Nash</b> chỉ yêu cầu mỗi bên là phản ứng tốt nhất với các nước đi đang xảy ra. Không phải mọi Nash đều dùng chiến lược ưu thế.", "solution_concepts"),
    ("Một trò chơi có thể có bao nhiêu Cân bằng Nash thuần túy?",
     "Có thể có một, nhiều hoặc không có cân bằng Nash nào ở <b>chiến lược thuần túy</b>. (Một số trò chơi vẫn có cân bằng ở chiến lược hỗn hợp.)", "solution_concepts"),
    ("Tại sao Cân bằng Nash không nhất thiết là kết cục tốt nhất cho tất cả?",
     "Nash chỉ nói không ai muốn đổi <b>đơn phương</b>. Một kết cục khác có thể làm tất cả cùng tốt hơn nếu họ có thể phối hợp thay đổi chiến lược.", "solution_concepts"),
    ("Trò chơi hợp tác (cooperative game) là gì?",
     "Người chơi có thể lập liên minh hoặc ký các thỏa thuận ràng buộc để phối hợp hành động; ví dụ các nước OPEC phối hợp chính sách dầu mỏ.", "classifications"),
    ("Trò chơi phi hợp tác (non-cooperative game) là gì?",
     "Người chơi tự lựa chọn chiến lược độc lập, không dựa vào liên minh/thỏa thuận ràng buộc; ví dụ đấu thầu dự án kín.", "classifications"),
    ("Trò chơi tổng bằng không (zero-sum game) là gì?",
     "Tổng payoff của các bên là hằng số (thường quy ước bằng 0): phần lợi của người này đúng bằng phần mất của người kia. Ví dụ: poker, cá cược thể thao.", "classifications"),
    ("Trò chơi tổng khác không (non-zero-sum game) là gì?",
     "Tổng payoff có thể tăng hoặc giảm; các bên có thể cùng thắng hoặc cùng thua. Ví dụ: thương mại quốc tế có thể tạo lợi ích cho nhiều bên.", "classifications"),
    ("Trò chơi đồng thời (simultaneous game) là gì?",
     "Các bên chọn hành động mà không quan sát được lựa chọn hiện tại của đối thủ; ví dụ oẳn tù tì. 'Đồng thời' có thể là thực tế đồng thời hoặc không biết nước đi của nhau.", "classifications"),
    ("Trò chơi tuần tự (sequential game) là gì?",
     "Các bên hành động theo thứ tự và người đi sau có thể quan sát một phần hay toàn bộ nước đi trước; ví dụ cờ vua, cờ tướng.", "classifications"),
    ("Ba cặp phân loại cơ bản trong Lý thuyết trò chơi là gì?",
     "<b>Hợp tác ↔ Phi hợp tác</b>; <b>Tổng bằng không ↔ Tổng khác không</b>; <b>Đồng thời ↔ Tuần tự</b>.", "classifications"),
    ("Tình huống: Hai công ty đàm phán sáp nhập. Nếu cùng chia sẻ dữ liệu thật, thương vụ rất thành công. Nếu một bên giấu thông tin để chiếm ưu thế, bên kia chịu thiệt; nếu cả hai cùng giấu, thương vụ thất bại. Đây là trò chơi gì?",
     "<b>Thế lưỡng nan của tù nhân</b> (Prisoner's Dilemma).<br><br>Sự cám dỗ của lợi ích cá nhân ngắn hạn (giấu thông tin) ngăn các bên đạt lợi ích tập thể tối ưu: hợp tác chia sẻ.", "situations"),
    ("Tình huống: Trong đàm phán chia tài sản, một người chia tài sản thành hai phần, người còn lại được chọn phần mình thích trước. Quy tắc này là gì?",
     "<b>Quy tắc “Cắt và Chọn”</b> (Divide and Choose).<br><br>Quy tắc tạo công bằng dựa trên tư lợi: người cắt có động lực chia công bằng nhất có thể để phần còn lại của mình không quá tệ.", "situations"),
    ("Tình huống: Công đoàn và công ty đều tuyên bố sẽ đình công/đóng cửa nhà máy nếu không thỏa thuận trước nửa đêm, dù biết cả hai sẽ tổn hại nặng nếu điều đó xảy ra. Đây là trò chơi gì?",
     "<b>Trò chơi Con gà</b> (Chicken Game/Brinkmanship).<br><br>Mỗi bên cố tỏ ra cứng rắn để ép đối phương nhượng bộ (bẻ lái) trước, nhằm tránh thảm họa chung.", "situations"),
    ("Tình huống: Sau nhiều vòng thương thảo giá, bên mua và bán chốt $100. Cả hai không hoàn toàn hài lòng, nhưng biết rằng đơn phương đòi đổi giá sẽ khiến đối tác bỏ đi và làm mình tệ hơn. Trạng thái này là gì?",
     "<b>Cân bằng Nash</b> (Nash Equilibrium).<br><br>Đây là trạng thái ổn định: không bên nào có động lực đơn phương thay đổi, vì thay đổi chỉ làm kết quả của chính họ tệ đi.", "situations"),
    ("Tình huống: Hai bên không chỉ tranh giá mà còn thương lượng thời hạn thanh toán, dịch vụ hậu mãi và cam kết số lượng để cả hai cùng có lợi hơn. Đây minh họa loại trò chơi nào?",
     "<b>Trò chơi tổng khác không</b> (Non-Zero-Sum Game).<br><br>Đây là đàm phán tích hợp (integrative negotiation): mở rộng “chiếc bánh” lợi ích thay vì chỉ chia một chiếc bánh có kích thước cố định.", "situations"),
    ("Tình huống: Người bán đưa mức giá đầu tiên cực cao làm mỏ neo. Người mua biết giá vô lý nhưng vẫn dùng nó làm cơ sở cho các bước trả giá sau. Đây minh họa lợi thế nào?",
     "<b>Lợi thế người đi trước</b> (First-mover Advantage).<br><br>Trong điều kiện thông tin không hoàn hảo, hành động đầu tiên thiết lập khung tham chiếu và buộc đối thủ phản ứng dựa trên khung đó.", "situations"),
    ("Tình huống: Bạn đàm phán mua xe cũ nhưng đã có một lựa chọn tốt tương đương ở cửa hàng bên cạnh nếu không mua được chiếc này. Khái niệm nào diễn tả sức mạnh đàm phán của bạn?",
     "<b>BATNA</b> (Best Alternative to a Negotiated Agreement).<br><br>Đây là phương án thay thế/điểm dừng (outside option). Sức mạnh đàm phán tăng theo chất lượng lựa chọn bạn có nếu đàm phán hiện tại thất bại.", "situations"),
    ("Tình huống: Một doanh nghiệp lớn và một doanh nghiệp nhỏ trong cùng khu công nghiệp đàm phán chia chi phí xây cơ sở hạ tầng chung.",
     "<b>Bản chất:</b> Khắc phục vấn đề <b>kẻ đi lậu vé</b> (free-rider) trong hàng hóa công cộng.<br><br><b>Player A — DN lớn:</b> Đe dọa không làm dự án nếu B không góp; hoặc trả 70–80% nếu lợi ích cận biên vẫn lớn hơn chi phí.<br><b>Player B — DN nhỏ:</b> Chỉ góp 20–30% theo lợi ích thực nhận, hoặc đề xuất chia theo doanh thu sau vận hành.<br><br><b>Gợi ý:</b> Ngăn trục lợi và tối ưu lợi ích cận biên mỗi bên.", "negotiation_cases"),
    ("Tình huống: Một ứng viên cấp cao xuất sắc đàm phán lương với tập đoàn đang cần người gấp.",
     "<b>Bản chất:</b> Trò chơi tuần tự với hiệu ứng mỏ neo.<br><br><b>Player A — Ứng viên:</b> Chủ động neo kỳ vọng cao bằng dữ liệu thị trường và BATNA mạnh (có offer đối thủ).<br><b>Player B — Nhà tuyển dụng:</b> Không phản hồi trực tiếp con số; chuyển sang cổ phiếu thưởng, phúc lợi và lộ trình thăng tiến để mở rộng chiếc bánh.<br><br><b>Gợi ý:</b> Dùng mỏ neo và chuyển từ tổng bằng không sang tổng khác không.", "negotiation_cases"),
    ("Tình huống: Trong thương vụ M&A, bên mua nghi ngờ chất lượng doanh nghiệp bán không đúng như báo cáo tài chính.",
     "<b>Bản chất:</b> Bất cân xứng thông tin và <b>thị trường xe chanh</b> (Lemons Problem).<br><br><b>Player A — Bên bán:</b> Phát tín hiệu uy tín bằng earn-out: chấp nhận một phần giá trả sau tùy hiệu suất thực tế.<br><b>Player B — Bên mua:</b> Sàng lọc bằng kiểm toán độc lập chi tiết và điều khoản bồi thường pháp lý nghiêm khắc.<br><br><b>Gợi ý:</b> Kết hợp signaling và screening để cân bằng thông tin.", "negotiation_cases"),
    ("Tình huống: Hai sàn TMĐT lớn đàm phán ngầm ngừng chiến dịch phá giá hủy diệt để giành thị phần.",
     "<b>Bản chất:</b> Thoát Cân bằng Nash xấu của Thế lưỡng nan tù nhân trong trò chơi lặp lại.<br><br><b>Player A — Sàn A:</b> Tăng giá trước ở ngành nhỏ để phát thiện chí; price-matching để giảm động lực phá giá.<br><b>Player B — Sàn B:</b> Tăng giá tương ứng và chuyển cạnh tranh sang chất lượng dịch vụ để giữ biên lợi nhuận.<br><br><b>Gợi ý:</b> Tit-for-Tat có lòng vị tha hỗ trợ hợp tác dài hạn.", "negotiation_cases"),
    ("Tình huống: Nhà sản xuất và đại lý toàn quốc đàm phán phân phối độc quyền một sản phẩm công nghệ mới.",
     "<b>Bản chất:</b> Thiết bị cam kết ràng buộc tự nguyện (commitment devices).<br><br><b>Player A — Nhà sản xuất:</b> Yêu cầu doanh số tối thiểu theo quý để đại lý tập trung bán, không phân phối chéo.<br><b>Player B — Đại lý:</b> Đòi độc quyền địa lý và phạt đền lớn nếu nhà sản xuất tự mở kênh trực tiếp.<br><br><b>Gợi ý:</b> Tạo chi phí chuyển đổi cao để ngăn hành vi cơ hội.", "negotiation_cases"),
    ("Tình huống: Hai tập đoàn đối thủ tranh chấp bản quyền công nghệ; cả hai đe dọa kiện ra tòa quốc tế, tốn hàng triệu USD.",
     "<b>Bản chất:</b> Trò chơi Con gà và brinkmanship.<br><br><b>Player A — Bên bị cho là vi phạm:</b> Đe dọa kiện ngược hoặc kéo dài tố tụng để bào mòn đối thủ, ép cấp phép rẻ.<br><b>Player B — Bên sở hữu:</b> Công bố bằng chứng không thể chối cãi và tự khóa đường lui bằng cam kết theo kiện đến cùng để ép cross-licensing.<br><br><b>Gợi ý:</b> Tự tước đường lui công khai để tín hiệu cam kết cứng rắn đáng tin.", "negotiation_cases"),
    ("Tình huống: Mua bán bất động sản khi người bán cần tiền trả nợ gấp và người mua cần mặt bằng kịp khai trương.",
     "<b>Bản chất:</b> Quản trị thông tin về hạn chót (deadline effects).<br><br><b>Player A — Người bán:</b> Đặt hard deadline kèm ưu đãi nhỏ để kích hoạt loss aversion của người mua.<br><b>Player B — Người mua:</b> Che giấu áp lực thời gian; đưa đề nghị take-it-or-leave-it sát giờ G để thử kiên nhẫn người bán.<br><br><b>Gợi ý:</b> Bất đối xứng chi phí cơ hội thời gian có thể quyết định giá.", "negotiation_cases"),
    ("Tình huống: Doanh nghiệp nợ 500 tỷ đồng không trả đúng hạn đàm phán giãn nợ với ngân hàng chủ nợ.",
     "<b>Bản chất:</b> Trò chơi cùng diệt vong chuyển thành hợp tác tối thiểu hóa tổn thất.<br><br><b>Player A — Doanh nghiệp:</b> Đe dọa nộp đơn phá sản, khiến ngân hàng có thể mất tài sản không thế chấp, để ép giảm lãi/giãn nợ.<br><b>Player B — Ngân hàng:</b> Đề xuất debt-to-equity swap để có quyền kiểm soát và hưởng lợi khi phục hồi.<br><br><b>Gợi ý:</b> Dùng nguy cơ cùng sụp đổ để tái cấu trúc quyền lực thương lượng.", "negotiation_cases"),
    ("Tình huống: Chủ đầu tư đô thị đàm phán với hộ dân cuối cùng đòi đền bù gấp 10 lần giá thị trường.",
     "<b>Bản chất:</b> Vấn đề kẻ trì hoãn bướng bỉnh (holdout problem).<br><br><b>Player A — Chủ đầu tư:</b> Đe dọa đổi thiết kế đi vòng để xóa quyền phủ quyết, hoặc thưởng tiến độ theo nhóm để tạo áp lực nội bộ.<br><b>Player B — Hộ dân:</b> Tính chi phí thiết kế lại và thời gian trễ để đòi mức cao nhất nhưng không vượt giới hạn đó.<br><br><b>Gợi ý:</b> Đừng vượt chi phí thay thế cận biên của đối phương để tránh bị cô lập.", "negotiation_cases"),
    ("Tình huống: Năm doanh nghiệp nhỏ lập liên minh mua chung nguyên liệu để ép giá nhà cung cấp.",
     "<b>Bản chất:</b> Phân chia thặng dư trong trò chơi hợp tác.<br><br><b>Player A — DN lớn nhất:</b> Đòi quyền phân bổ đơn hàng/thu phí vận hành để bù rủi ro bảo lãnh tài chính.<br><b>Player B — Các DN nhỏ:</b> Đòi phân chia giảm giá theo tỷ lệ sản lượng và giữ quyền rút lui.<br><br><b>Gợi ý:</b> Dùng <b>giá trị Shapley</b> để phân phối thặng dư hợp tác công bằng.", "negotiation_cases"),
    ("Tình huống: Nhà cung cấp hạt nhựa và nhà sản xuất bao bì ký hợp đồng dài hạn khi giá dầu biến động mạnh.",
     "<b>Bản chất:</b> Hợp đồng chia sẻ rủi ro (risk-sharing contracts).<br><br><b>Player A — Nhà cung cấp:</b> Đề xuất lượng mua tối thiểu cùng giá sàn/trần để bảo hiểm lợi nhuận nhà máy.<br><b>Player B — Nhà sản xuất:</b> Đòi index pricing linh hoạt theo giá thị trường thế giới để không bị khóa vào giá bất lợi.<br><br><b>Gợi ý:</b> Cơ chế tự điều chỉnh theo chỉ số khách quan tránh tranh cãi lặp lại.", "negotiation_cases"),
    ("Tình huống: Ba tập đoàn công nghệ đấu giá kín để mua startup AI có công nghệ độc quyền.",
     "<b>Bản chất:</b> Lời nguyền người chiến thắng trong đấu giá giá trị chung.<br><br><b>Player A — Người mua:</b> Bid shading: đặt thấp hơn định giá tối đa một biên an toàn vì thiếu thông tin.<br><b>Player B — Startup:</b> Dùng nhiều vòng đấu giá và tiết lộ nhỏ giọt tin tốt để kích hoạt FOMO.<br><br><b>Gợi ý:</b> Người trả cao nhất thường là người đánh giá tài sản quá cao nhất.", "negotiation_cases"),
    ("Tình huống: Điện thoại bị nổ gây thương tích nhẹ; khách hàng dọa đăng video, nhãn hàng muốn giải quyết êm đẹp.",
     "<b>Bản chất:</b> Đánh đổi tổn thất danh tiếng phi vật chất và chi phí tài chính trực tiếp.<br><br><b>Player A — Khách hàng:</b> Đe dọa truyền thông để đòi bồi thường vượt thiệt hại thực tế.<br><b>Player B — Nhãn hàng:</b> Bồi thường bảo mật kèm NDA, hoặc công khai xin lỗi minh bạch khi yêu sách phi lý để tranh thủ công chúng.<br><br><b>Gợi ý:</b> Biến vụ việc thành thông điệp tích cực về trách nhiệm thương hiệu.", "negotiation_cases"),
    ("Tình huống: Gia đình phân chia kỷ vật và tranh ảnh của tổ tiên mà muốn tránh rạn nứt tình cảm.",
     "<b>Bản chất:</b> Phân chia công bằng phi tiền tệ (fair division/cake-cutting).<br><br><b>Player A — Người phân chia:</b> Chia thành phần tương đương về cảm tính và vật chất theo sở thích thành viên.<br><b>Player B — Người nhận:</b> Chọn trước theo Divide and Choose; hoặc đấu giá nội bộ bằng điểm, người giá cao nhất giữ món đồ và bù tiền cho người khác.<br><br><b>Gợi ý:</b> Dùng cơ chế toán học công bằng để giảm tị hiềm.", "negotiation_cases"),
    ("Tình huống: Thương hiệu thời trang kinh doanh tốt tại TTTM đàm phán gia hạn hợp đồng thuê.",
     "<b>Bản chất:</b> Ngoại ứng tích cực và định giá hai bên.<br><br><b>Player A — Chủ trung tâm:</b> Đe dọa tăng giá theo lượng khách và ám chỉ có đối thủ chờ thế chỗ.<br><b>Player B — Khách thuê:</b> Chứng minh vai trò anchor tenant thu hút khách; đe dọa chuyển sang TTTM đối thủ khiến khách hiện tại giảm.<br><br><b>Gợi ý:</b> Định vị mình là nguồn tạo lưu lượng khách để giảm sức mạnh định giá đối tác.", "negotiation_cases"),
    ("Tình huống: Ban tổ chức Ngoại hạng Anh bán bản quyền phát sóng cho các đài truyền hình lớn tại Việt Nam.",
     "<b>Bản chất:</b> Phân mảnh thị trường để khai thác thặng dư tiêu dùng tối đa.<br><br><b>Player A — Ban tổ chức:</b> Chia gói TV, Internet, highlight để tối đa hóa doanh thu từng phân khúc.<br><b>Player B — Nhà đài:</b> Liên minh mua gói lớn, hoặc dồn lực đấu thầu độc quyền gói quan trọng nhất để khác biệt hóa.<br><br><b>Gợi ý:</b> Phân mảnh sản phẩm giúp khai thác tối đa thặng dư người mua lẻ.", "negotiation_cases"),
    ("Tình huống: Hội đồng quản trị chấm dứt sớm hợp đồng CEO do bất đồng chiến lược.",
     "<b>Bản chất:</b> Giảm rủi ro kiện tụng và bảo vệ danh tiếng tổ chức.<br><br><b>Player A — Doanh nghiệp:</b> Đề xuất outplacement và thư giới thiệu uy tín để giảm nguy cơ kiện/tung bí mật.<br><b>Player B — CEO:</b> Đàm phán kéo dài bảo hiểm sức khỏe và quyền mua cổ phiếu chưa thực hiện, đổi lại bàn giao toàn diện.<br><br><b>Gợi ý:</b> Biến chấm dứt thành giao dịch hợp tác bảo vệ uy tín đôi bên.", "negotiation_cases"),
    ("Tình huống: Khách hàng và công ty gia công đàm phán chi phí ứng dụng quản lý doanh nghiệp phức tạp.",
     "<b>Bản chất:</b> Phân bổ rủi ro thực thi trong hợp đồng dịch vụ không hoàn hảo.<br><br><b>Player A — Khách hàng:</b> Đòi fixed price để chuyển rủi ro thời gian/nhân lực cho nhà thầu.<br><b>Player B — Nhà thầu:</b> Đề xuất Time & Materials và định nghĩa change request tính phí cao.<br><br><b>Gợi ý:</b> Cơ chế giá phải phản ánh đúng phân bổ rủi ro thực thi.", "negotiation_cases"),
    ("Tình huống: Founder startup đàm phán vòng Series A với quỹ đầu tư mạo hiểm về sở hữu và quyền kiểm soát.",
     "<b>Bản chất:</b> Phân tách quyền lợi kinh tế và quyền kiểm soát chiến lược.<br><br><b>Player A — Founder:</b> Giữ quyền kiểm soát HĐQT qua cổ phần ưu đãi biểu quyết, có thể nhận định giá thấp hơn chút.<br><b>Player B — Quỹ:</b> Cài anti-dilution và liquidation preference để bảo toàn vốn trong kịch bản xấu.<br><br><b>Gợi ý:</b> Định giá chỉ là một phần; điều khoản cấu trúc mới quyết định quyền lực thực tế.", "negotiation_cases"),
    ("Tình huống: Tập đoàn Đức chuyển giao công nghệ động cơ điện cho đối tác lớn tại Việt Nam.",
     "<b>Bản chất:</b> Đổi tài sản trí tuệ lấy tiếp cận thị trường nhanh.<br><br><b>Player A — Tập đoàn công nghệ:</b> Chỉ chuyển công nghệ cũ hoặc lập liên doanh nắm đa số để bảo vệ bí mật lõi.<br><b>Player B — DN bản địa:</b> Dùng hiểu biết thị trường/chính sách làm đòn bẩy để đòi chuyển giao từng phần và đào tạo nhân lực.<br><br><b>Gợi ý:</b> Kết hợp tài sản công nghệ với rào cản chính sách/thương mại của bên kia.", "negotiation_cases"),
    ("Tình huống: Trưởng phòng Marketing và R&D tranh 10 triệu USD ngân sách còn lại của tập đoàn.",
     "<b>Bản chất:</b> Trò chơi quyền lực nội bộ với nguồn lực hữu hạn.<br><br><b>Player A — Marketing:</b> Gắn ngân sách với tăng trưởng doanh thu và ROI ngắn hạn dễ thấy.<br><b>Player B — R&D:</b> Nhấn mạnh lợi thế dài hạn và rủi ro tụt hậu công nghệ nếu thiếu nghiên cứu.<br><br><b>Gợi ý:</b> Lồng khung lợi ích phòng ban vào mục tiêu tối thượng của tập đoàn.", "negotiation_cases"),
    ("Tình huống: Thương hiệu trà sữa nhượng quyền cho nhà đầu tư lớn tại tỉnh biên giới.",
     "<b>Bản chất:</b> Giải quyết mâu thuẫn người ủy quyền – người đại lý (agency problem).<br><br><b>Player A — Bên nhượng quyền:</b> Dùng phí cố định và giám sát POS để tránh giấu doanh thu giảm hoa hồng.<br><b>Player B — Bên nhận quyền:</b> Đòi độc quyền địa lý và nguồn nguyên liệu chất lượng với giá ưu đãi.<br><br><b>Gợi ý:</b> Đồng bộ động cơ lợi nhuận của hai bên.", "negotiation_cases"),
    ("Tình huống: Hộ nông nghiệp hữu cơ nhỏ đàm phán đưa rau cao cấp vào chuỗi siêu thị toàn quốc.",
     "<b>Bản chất:</b> Ứng phó sức ép từ kênh phân phối thống lĩnh.<br><br><b>Player A — Nhà sản xuất:</b> Xây thương hiệu trên mạng xã hội để kéo khách đến siêu thị (pull strategy), hoặc ký gửi để chứng minh sức mua.<br><b>Player B — Siêu thị:</b> Đòi slotting fees cao và kéo dài thanh toán để chiếm dụng vốn nhà cung cấp.<br><br><b>Gợi ý:</b> Chuyển Push sang Pull để cân bằng thương lượng khi quy mô nhỏ.", "negotiation_cases"),
    ("Tình huống: Hai hộ hàng xóm tranh chấp dải đất ranh giới 20 cm, có nguy cơ kiện tụng/bạo lực.",
     "<b>Bản chất:</b> Trò chơi tổng âm: chi phí tranh chấp lớn hơn giá trị đất.<br><br><b>Player A — Hộ A:</b> Mua phần đất với giá thị trường cộng thiện chí để dứt điểm và xây nhà.<br><b>Player B — Hộ B:</b> Chấp nhận bán hoặc cùng góp xây hàng rào, vì ra tòa làm giảm giá trị giao dịch tương lai của cả hai nhà.<br><br><b>Gợi ý:</b> Thỏa thuận sớm bảo toàn thặng dư hơn kiện tụng kéo dài.", "negotiation_cases"),
    ("Tình huống: Tập đoàn đổi thương hiệu cần mua tên miền .com từ một cá nhân đầu cơ tên miền.",
     "<b>Bản chất:</b> Che giấu thông tin về mức sẵn lòng chi trả.<br><br><b>Player A — Doanh nghiệp:</b> Dùng đại diện/tài khoản ẩn danh để hỏi mua, không lộ danh tính tập đoàn nhằm tránh bị đẩy giá.<br><b>Player B — Đầu cơ:</b> Định giá theo khan hiếm và hoạt động đăng ký nhãn hiệu; neo giá cao rồi giảm có hạn chót.<br><br><b>Gợi ý:</b> Bất đối xứng thông tin về khả năng tài chính người mua quyết định giá tài sản độc quyền.", "negotiation_cases"),
]

CSS = """
.card { font-family: Arial, sans-serif; font-size: 20px; line-height: 1.5;
  text-align: left; color: #1f2937; background: #f8fafc; }
.nightMode .card { color: #e5e7eb; background: #111827; }
.question { font-size: 25px; font-weight: 700; color: #1d4ed8; text-align: center; }
.answer { margin-top: 10px; }
.label { display: inline-block; margin-top: 14px; padding: 3px 9px; border-radius: 12px;
  color: #475569; background: #e2e8f0; font-size: 12px; }
.nightMode .label { color: #cbd5e1; background: #334155; }
"""


def checksum(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:8], 16)


def guid(question: str) -> str:
    return hashlib.sha1(f"game-theory:{question}".encode("utf-8")).hexdigest()[:10]


def front(question: str, tag: str) -> str:
    label = tag.replace("_", " ").title()
    return f'<div class="question">{html.escape(question)}</div><div class="label">{html.escape(label)}</div>'


def back(answer: str, tag: str) -> str:
    label = tag.replace("_", " ").title()
    return f'<div class="answer">{answer}</div><div class="label">{html.escape(label)}</div>'


def write_preview() -> None:
    """Create the human-readable preview from the same card data as Anki."""
    labels = {
        "overview": "Tổng quan", "core_elements": "Bốn yếu tố cấu thành",
        "assumptions": "Hai giả định nền tảng", "solution_concepts": "Khái niệm giải bài toán",
        "classifications": "Phân loại trò chơi", "situations": "Tình huống ứng dụng",
        "negotiation_cases": "25 tình huống đàm phán & chiến thuật",
    }
    parts = ["# Xem trước thẻ — Lý thuyết trò chơi: Nền tảng\n",
             f"Tài liệu này liệt kê chính xác mặt trước và mặt sau của {len(CARDS)} thẻ trong tệp Anki.\n"]
    previous_tag = None
    for number, (question, answer, tag) in enumerate(CARDS, start=1):
        if tag != previous_tag:
            parts.append(f"## {labels[tag]}\n")
            previous_tag = tag
        answer_markdown = answer.replace("<br><br>", "\n\n").replace("<br>", "\n")
        answer_markdown = answer_markdown.replace("<b>", "**").replace("</b>", "**")
        parts.append(f"### Thẻ {number:02d}\n\n**Mặt trước:** {question}\n\n**Mặt sau:** {answer_markdown}\n")
    (ROOT / "card.md").write_text("\n".join(parts), encoding="utf-8")


def build() -> None:
    if not TEMPLATE.is_file():
        raise FileNotFoundError(f"Missing Anki schema template: {TEMPLATE}")
    now = int(time.time())
    with tempfile.TemporaryDirectory(prefix="game_theory_anki_") as temp_dir:
        database = Path(temp_dir) / "collection.anki2"
        with zipfile.ZipFile(TEMPLATE) as package:
            database.write_bytes(package.read("collection.anki2"))

        connection = sqlite3.connect(database)
        try:
            models_raw, decks_raw = connection.execute("SELECT models, decks FROM col").fetchone()
            model = deepcopy(next(iter(json.loads(models_raw).values())))
            model.update({"id": str(MODEL_ID), "did": DECK_ID, "name": MODEL_NAME, "css": CSS, "mod": now})

            source_decks = json.loads(decks_raw)
            source_deck = next(deck for key, deck in source_decks.items() if key != "1")
            deck = deepcopy(source_deck)
            deck.update({"id": DECK_ID, "name": DECK_NAME,
                         "desc": "32 thẻ hỏi–đáp về nền tảng và tình huống Lý thuyết trò chơi.",
                         "mod": now, "usn": -1, "lrnToday": [0, 0], "newToday": [0, 0],
                         "revToday": [0, 0], "timeToday": [0, 0]})

            conf = json.loads(connection.execute("SELECT conf FROM col").fetchone()[0])
            conf.update({"activeDecks": [DECK_ID], "curDeck": DECK_ID,
                         "curModel": str(MODEL_ID), "nextPos": len(CARDS) + 1})
            tags = {tag: 0 for *_rest, tag in CARDS}

            for table in ("cards", "notes", "revlog", "graves"):
                connection.execute(f"DELETE FROM {table}")
            connection.execute("UPDATE col SET mod=?, scm=?, conf=?, models=?, decks=?, tags=?",
                               (now * 1000, now * 1000, json.dumps(conf),
                                json.dumps({str(MODEL_ID): model}),
                                json.dumps({"1": source_decks["1"], str(DECK_ID): deck}), json.dumps(tags)))

            base_id = now * 1000
            for position, (question, answer, tag) in enumerate(CARDS, start=1):
                question_html = front(question, tag)
                note_id = base_id + position * 10
                connection.execute("INSERT INTO notes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (note_id, guid(question), MODEL_ID, now, -1, f" {tag} game_theory ",
                     "\x1f".join((question_html, back(answer, tag))), question_html,
                     checksum(question_html), 0, ""))
                connection.execute("INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (note_id + 1, note_id, DECK_ID, 0, now, -1, 0, 0, position,
                     0, 0, 0, 0, 0, 0, 0, 0, ""))
            connection.commit()
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Anki database integrity check failed")
        finally:
            connection.close()

        with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as package:
            package.write(database, "collection.anki2")
            package.writestr("media", "{}")
    print(f"Created {OUTPUT.name}: {len(CARDS)} notes, {len(CARDS)} cards")
    write_preview()


if __name__ == "__main__":
    build()
